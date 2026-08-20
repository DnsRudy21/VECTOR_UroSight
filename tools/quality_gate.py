"""Repeatable operational quality gate for a frozen local detector.

This checks reproducibility, latency, and failures. It does not estimate accuracy
because no ground-truth annotations are consumed here.
"""

import argparse
import hashlib
import json
import statistics
import time
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.inference.local_yolo_provider import LocalYoloProvider


def _fingerprint(analysis) -> str:
    payload = [
        (d.class_name, round(d.confidence, 6), round(d.bbox.x, 3), round(d.bbox.y, 3),
         round(d.bbox.width, 3), round(d.bbox.height, 3))
        for d in analysis.detections
    ]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def run_gate(model: Path, images: list[Path], rounds: int, confidence: float) -> dict:
    provider = LocalYoloProvider(model, confidence)
    records: dict[str, list[dict]] = {path.name: [] for path in images}
    failures = []
    for round_number in range(1, rounds + 1):
        for path in images:
            started = time.perf_counter()
            try:
                analysis = provider.predict(path)
                records[path.name].append({"round": round_number,
                    "elapsed_ms": (time.perf_counter() - started) * 1000,
                    "detections": len(analysis.detections), "fingerprint": _fingerprint(analysis)})
            except Exception as exc:
                failures.append({"round": round_number, "image": path.name,
                                 "error_type": type(exc).__name__})
    latencies = [record["elapsed_ms"] for values in records.values() for record in values]
    stable = all(len({record["fingerprint"] for record in values}) <= 1 for values in records.values())
    return {"model": model.name, "rounds": rounds, "images": len(images), "requests": rounds * len(images),
            "confidence": confidence, "deterministic_across_rounds": stable,
            "failures": failures, "latency_ms": {"median": statistics.median(latencies) if latencies else None,
            "p95": sorted(latencies)[max(0, int(len(latencies)*.95)-1)] if latencies else None,
            "maximum": max(latencies) if latencies else None}, "per_image": records,
            "scope": "Operational reproducibility only; not an accuracy or clinical validation metric."}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--confidence", type=float, default=.25)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    images = sorted(path for path in args.images.iterdir() if path.suffix.lower() in {".jpg", ".jpeg", ".png"})[:6]
    if not images: raise ValueError("No compatible images found for the quality gate.")
    result = run_gate(args.model, images, args.rounds, args.confidence)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("requests", "deterministic_across_rounds", "failures", "latency_ms")}, indent=2))
    return 0 if not result["failures"] and result["deterministic_across_rounds"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
