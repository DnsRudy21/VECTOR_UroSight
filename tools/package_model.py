from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def best_row(results_csv: Path) -> dict[str, str]:
    with results_csv.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("results.csv no contiene épocas.")
    key = "metrics/mAP50-95(B)"
    if key not in rows[0]:
        raise ValueError(f"No existe la métrica requerida: {key}")
    return max(rows, key=lambda row: float(row[key]))


def package(run: Path, destination: Path, artifact_root: Path, dataset_summary: Path, *, threshold: float) -> dict:
    weights = run / "weights" / "best.pt"
    results = run / "results.csv"
    if not weights.is_file() or not results.is_file():
        raise FileNotFoundError("La corrida no contiene best.pt y results.csv.")
    for target in (destination, artifact_root):
        if target.exists() and any(target.iterdir()):
            raise FileExistsError(f"El destino final no está vacío: {target}")
        target.mkdir(parents=True, exist_ok=True)
    row = best_row(results)
    import torch
    import ultralytics
    metric_keys = {
        "precision": "metrics/precision(B)", "recall": "metrics/recall(B)",
        "map50": "metrics/mAP50(B)", "map50_95": "metrics/mAP50-95(B)",
    }
    metadata = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture": "YOLO11n", "task": "object-detection", "imgsz": 320,
        "classes": ["eryth", "leuko", "epith", "epithn", "cast", "cryst", "mycete"],
        "dataset": "VECTOR_dataset derived from USE", "recommended_threshold": threshold,
        "selection_split": "validation", "best_epoch": int(row["epoch"]),
        "validation_metrics": {name: float(row[key]) for name, key in metric_keys.items()},
        "weights_sha256": sha256(weights), "clinical_validation": False,
        "ultralytics_version": ultralytics.__version__, "torch_version": torch.__version__,
    }
    shutil.copy2(weights, destination / "best.pt")
    (destination / "model_metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    shutil.copy2(weights, artifact_root / "best.pt")
    shutil.copy2(results, artifact_root / "results.csv")
    shutil.copy2(dataset_summary, artifact_root / "dataset_summary.json")
    for name in ("results.png", "confusion_matrix.png", "confusion_matrix_normalized.png", "PR_curve.png", "F1_curve.png", "P_curve.png", "R_curve.png", "labels.jpg"):
        source = run / name
        if source.is_file():
            shutil.copy2(source, artifact_root / name)
    args_yaml = run / "args.yaml"
    if args_yaml.is_file():
        shutil.copy2(args_yaml, artifact_root / "training_config.yaml")
    (artifact_root / "metrics.json").write_text(json.dumps(metadata["validation_metrics"], indent=2), encoding="utf-8")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Empaqueta una corrida YOLO final sin sobrescribir artefactos.")
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--model-destination", type=Path, default=Path("models/vector_urosight"))
    parser.add_argument("--artifact-destination", type=Path, default=Path("artifacts/model_final"))
    parser.add_argument("--dataset-summary", type=Path, default=Path("data_processed/VECTOR_dataset/dataset_summary.json"))
    parser.add_argument("--threshold", type=float, required=True)
    args = parser.parse_args()
    print(json.dumps(package(args.run, args.model_destination, args.artifact_destination, args.dataset_summary, threshold=args.threshold), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
