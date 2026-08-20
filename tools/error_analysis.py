from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    left, top = max(a[0], b[0]), max(a[1], b[1])
    right, bottom = min(a[2], b[2]), min(a[3], b[3])
    intersection = max(0.0, right - left) * max(0.0, bottom - top)
    if not intersection:
        return 0.0
    area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    return intersection / (area_a + area_b - intersection)


def match_detections(truth: list[dict], predictions: list[dict], threshold: float = 0.5) -> dict:
    unmatched_truth = set(range(len(truth)))
    unmatched_predictions = set(range(len(predictions)))
    true_positives: list[tuple[int, int]] = []
    candidates = sorted(
        ((iou(t["box"], p["box"]), ti, pi) for ti, t in enumerate(truth) for pi, p in enumerate(predictions) if t["class_id"] == p["class_id"]),
        reverse=True,
    )
    for overlap, truth_index, prediction_index in candidates:
        if overlap < threshold:
            break
        if truth_index in unmatched_truth and prediction_index in unmatched_predictions:
            unmatched_truth.remove(truth_index); unmatched_predictions.remove(prediction_index)
            true_positives.append((truth_index, prediction_index))
    misclassifications = []
    cross_candidates = sorted(
        ((iou(truth[ti]["box"], predictions[pi]["box"]), ti, pi) for ti in unmatched_truth for pi in unmatched_predictions if truth[ti]["class_id"] != predictions[pi]["class_id"]),
        reverse=True,
    )
    for overlap, truth_index, prediction_index in cross_candidates:
        if overlap < threshold:
            break
        if truth_index in unmatched_truth and prediction_index in unmatched_predictions:
            unmatched_truth.remove(truth_index); unmatched_predictions.remove(prediction_index)
            misclassifications.append((truth_index, prediction_index))
    return {"true_positives": true_positives, "false_negatives": sorted(unmatched_truth), "false_positives": sorted(unmatched_predictions), "misclassifications": misclassifications}


def yolo_truth(label: Path, width: int, height: int) -> list[dict]:
    result = []
    for line in label.read_text(encoding="utf-8-sig").splitlines():
        class_id, xc, yc, bw, bh = map(float, line.split())
        result.append({"class_id": int(class_id), "box": ((xc - bw / 2) * width, (yc - bh / 2) * height, (xc + bw / 2) * width, (yc + bh / 2) * height)})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Analiza TP, FP, FN y confusiones sobre un split YOLO.")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--split", default="test")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--confidence", type=float, default=0.25)
    parser.add_argument("--iou", type=float, default=0.5)
    args = parser.parse_args()
    from PIL import Image
    from ultralytics import YOLO
    model = YOLO(str(args.model))
    image_dir, label_dir = args.dataset / "images" / args.split, args.dataset / "labels" / args.split
    totals = Counter(); confusions = Counter(); per_class: dict[str, Counter] = {name: Counter() for name in model.names.values()}; examples: dict[str, list[str]] = {key: [] for key in ("true_positive", "false_positive", "false_negative", "misclassification")}
    for image in sorted(image_dir.glob("*")):
        with Image.open(image) as opened:
            width, height = opened.size
        truth = yolo_truth(label_dir / f"{image.stem}.txt", width, height)
        prediction_result = model.predict(str(image), conf=args.confidence, imgsz=320, device="cpu", verbose=False)[0]
        predictions = [{"class_id": int(box.cls.item()), "box": tuple(box.xyxy[0].tolist()), "confidence": float(box.conf.item())} for box in prediction_result.boxes]
        matched = match_detections(truth, predictions, args.iou)
        mapping = {"true_positive": "true_positives", "false_positive": "false_positives", "false_negative": "false_negatives", "misclassification": "misclassifications"}
        for singular, key in mapping.items():
            count = len(matched[key]); totals[singular] += count
            if count and len(examples[singular]) < 20:
                examples[singular].append(image.name)
        for truth_index, _ in matched["true_positives"]:
            per_class[model.names[truth[truth_index]["class_id"]]]["true_positive"] += 1
        for truth_index in matched["false_negatives"]:
            per_class[model.names[truth[truth_index]["class_id"]]]["false_negative"] += 1
        for prediction_index in matched["false_positives"]:
            per_class[model.names[predictions[prediction_index]["class_id"]]]["false_positive"] += 1
        for truth_index, prediction_index in matched["misclassifications"]:
            true_name = model.names[truth[truth_index]["class_id"]]
            predicted_name = model.names[predictions[prediction_index]["class_id"]]
            confusions[f"{true_name}->{predicted_name}"] += 1
            per_class[true_name]["misclassified"] += 1
    payload = {"confidence": args.confidence, "iou": args.iou, "totals": dict(totals), "confusions": dict(confusions.most_common()), "per_class": {key: dict(value) for key, value in per_class.items()}, "example_images": examples}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "error_analysis.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload["totals"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
