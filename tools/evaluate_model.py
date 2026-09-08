from __future__ import annotations

import argparse
import csv
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path


def metrics_payload(metrics, names: dict[int, str], *, split: str, confidence: float | None,
                    augment: bool = False) -> tuple[dict, list[dict]]:
    box = metrics.box
    per_class = []
    maps = list(box.maps)
    precision = list(box.p)
    recall = list(box.r)
    ap50 = list(box.ap50)
    class_indices = list(getattr(box, "ap_class_index", range(len(precision))))
    positions = {int(class_id): position for position, class_id in enumerate(class_indices)}
    support = list(getattr(metrics, "nt_per_class", [0] * len(names)))
    for class_id, name in sorted(names.items()):
        position = positions.get(class_id)
        per_class.append({
            "class_id": class_id,
            "class_name": name,
            "support": int(support[class_id]) if class_id < len(support) else 0,
            "precision": float(precision[position]) if position is not None else 0.0,
            "recall": float(recall[position]) if position is not None else 0.0,
            "ap50": float(ap50[position]) if position is not None else 0.0,
            "map50_95": float(maps[class_id]) if class_id < len(maps) else 0.0,
        })
    summary = {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "split": split,
        "confidence": confidence,
        "augment": augment,
        "precision": float(box.mp),
        "recall": float(box.mr),
        "map50": float(box.map50),
        "map50_95": float(box.map),
        "fitness": float(metrics.fitness),
        "speed_ms_per_image": {key: float(value) for key, value in metrics.speed.items()},
    }
    f1_curve = getattr(box, "f1_curve", None)
    confidence_axis = getattr(box, "px", None)
    if f1_curve is not None and confidence_axis is not None and len(confidence_axis):
        mean_f1 = f1_curve.mean(0)
        best_index = int(mean_f1.argmax())
        summary["best_f1"] = float(mean_f1[best_index])
        summary["recommended_confidence"] = float(confidence_axis[best_index])
    return summary, per_class


def write_evaluation(output: Path, summary: dict, per_class: list[dict]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "metrics.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    with (output / "metrics_by_class.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=("class_id", "class_name", "support", "precision", "recall", "ap50", "map50_95"))
        writer.writeheader(); writer.writerows(per_class)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evalúa un checkpoint YOLO y persiste métricas reales.")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--split", choices=("val", "test"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--imgsz", type=int, default=320)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--confidence", type=float)
    parser.add_argument("--plots", action="store_true")
    parser.add_argument("--augment", action="store_true")
    args = parser.parse_args()
    from ultralytics import YOLO
    model = YOLO(str(args.model))
    kwargs = {"data": str(args.data), "split": args.split, "imgsz": args.imgsz, "batch": args.batch, "device": "cpu", "workers": 0, "plots": args.plots, "augment": args.augment, "project": str(args.output.parent.resolve()), "name": args.output.name, "exist_ok": True, "verbose": True}
    if args.confidence is not None:
        kwargs["conf"] = args.confidence
    metrics = model.val(**kwargs)
    summary, per_class = metrics_payload(metrics, model.names, split=args.split,
                                         confidence=args.confidence, augment=args.augment)
    summary.update(model_path=str(args.model.resolve()),
                   model_sha256=hashlib.sha256(args.model.read_bytes()).hexdigest(),
                   data_yaml=str(args.data.resolve()), imgsz=args.imgsz, batch=args.batch,
                   precision_recall_operating_point="Ultralytics smoothed max-F1 point; not fixed input confidence")
    write_evaluation(args.output, summary, per_class)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
