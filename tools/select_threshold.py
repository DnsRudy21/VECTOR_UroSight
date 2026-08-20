from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def f1(precision: float, recall: float) -> float:
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def select(rows: list[dict]) -> dict:
    if not rows:
        raise ValueError("No hay resultados de threshold.")
    return max(rows, key=lambda row: (row["f1"], row["recall"], -row["threshold"]))


def main() -> int:
    parser = argparse.ArgumentParser(description="Selecciona threshold exclusivamente sobre validación.")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--thresholds", type=float, nargs="+", default=(0.25, 0.35, 0.50))
    parser.add_argument("--imgsz", type=int, default=320)
    args = parser.parse_args()
    from ultralytics import YOLO
    model = YOLO(str(args.model))
    rows = []
    for threshold in args.thresholds:
        metrics = model.val(data=str(args.data), split="val", conf=threshold, imgsz=args.imgsz, batch=16, device="cpu", workers=0, plots=False, verbose=False, project=str(args.output.resolve()), name=f"threshold_{threshold:.2f}", exist_ok=True)
        precision, recall = float(metrics.box.mp), float(metrics.box.mr)
        rows.append({"threshold": threshold, "precision": precision, "recall": recall, "f1": f1(precision, recall), "map50": float(metrics.box.map50), "map50_95": float(metrics.box.map)})
    recommended = select(rows)
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "threshold_comparison.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    payload = {"selection_split": "validation", "criterion": "maximum global F1; recall then lower threshold as tie breakers", "recommended_threshold": recommended["threshold"], "results": rows}
    (args.output / "threshold_comparison.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
