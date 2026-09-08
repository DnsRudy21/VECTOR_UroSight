"""Presence-only synthetic QA; never computes clinical or detection metrics."""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import hashlib
import io
import json
from pathlib import Path
import time
import zipfile
from datetime import datetime, timezone
from importlib.metadata import version

from src.inference.local_yolo_provider import LocalYoloProvider
from src.services.analysis_service import AnalysisService
from src.services.export_service import export_csv, export_json


def presence_difference(expected: str, detected: set[str]) -> dict:
    visible = set(filter(None, expected.split("|")))
    return {"possibly_missed": sorted(visible - detected),
            "possibly_unsupported": sorted(detected - visible),
            "presence_consistent": visible == detected}


def run(pack: Path, images: Path, model: Path, output: Path,
        threshold: float = .44, imgsz: int = 448, augment: bool = True) -> dict:
    if output.exists():
        raise FileExistsError(f"Use a new output directory: {output}")
    with zipfile.ZipFile(pack) as archive:
        member = next(n for n in archive.namelist() if n.endswith('/review_per_image.csv'))
        rows = list(csv.DictReader(io.StringIO(archive.read(member).decode('utf-8-sig'))))
    filenames = [r['file'] for r in rows]
    if len(set(filenames)) != len(filenames) or any(Path(n).name != n for n in filenames):
        raise ValueError('Review filenames must be unique basenames')
    missing = [n for n in filenames if not (images / n).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing original images: {missing}")
    provider = LocalYoloProvider(model, confidence=threshold, imgsz=imgsz, augment=augment)
    metadata = {'purpose': 'synthetic QA only; not clinical ground truth',
                'started_at': datetime.now(timezone.utc).isoformat(),
                'ultralytics_version': version('ultralytics'), 'torch_version': version('torch'),
                'bbox_format': 'center x,y,width,height in original-image pixels',
                'model_path': str(model.resolve()),
                'model_sha256': hashlib.sha256(model.read_bytes()).hexdigest(),
                'pack_sha256': hashlib.sha256(pack.read_bytes()).hexdigest(),
                'names': provider._model.names, 'architecture': provider._model.model.yaml,
                'train_args': provider._model.ckpt.get('train_args'),
                'threshold': threshold, 'imgsz': imgsz, 'augment': augment,
                'max_detections': provider.max_detections,
                'provider': provider.display_name}
    output.mkdir(parents=True)
    (output / 'model_audit.json').write_text(json.dumps(metadata, indent=2, default=str), encoding='utf-8')
    comparisons = []
    service = AnalysisService(provider)
    with (output / 'results.jsonl').open('w', encoding='utf-8') as stream:
        for row in rows:
            path = images / row['file']
            start = time.perf_counter()
            study = service.analyze([path], source='Synthetic Silver QA')
            elapsed = (time.perf_counter() - start) * 1000
            analysis = study.images[0]
            detected = {d.raw_class for d in study.detections_for(analysis)}
            difference = presence_difference(row['reviewed_visible_classes'], detected)
            comparison = {'file': path.name, 'error': analysis.error,
                          'review_confidence': row['review_confidence'],
                          'historical_audit_status': row['audit_status'],
                          'detected': sorted(detected), **difference}
            if analysis.error:
                comparison.update(possibly_missed=None, possibly_unsupported=None, presence_consistent=None)
            record = {**comparison, 'image_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                      'wall_ms': elapsed, 'inference_ms': analysis.inference_ms,
                      'model_sha256': metadata['model_sha256'], 'provider': provider.display_name,
                      'threshold': threshold, 'imgsz': imgsz, 'augment': augment,
                      'detections': [asdict(d) for d in analysis.detections],
                      'raw_detections': [asdict(d) for d in analysis.raw_detections]}
            stream.write(json.dumps(record, default=str) + '\n'); stream.flush()
            comparisons.append(comparison)
            export_json(study, output / f'{path.stem}.json')
            export_csv(study, output / f'{path.stem}.csv')
            print(f'{len(comparisons)}/{len(rows)} {path.name}', flush=True)
    with (output / 'presence_comparison.csv').open('w', newline='', encoding='utf-8-sig') as handle:
        writer = csv.DictWriter(handle, fieldnames=comparisons[0].keys())
        writer.writeheader(); writer.writerows(comparisons)
    summary = {'images': len(rows), 'failed': sum(bool(r['error']) for r in comparisons),
               'presence_consistent': sum(r['presence_consistent'] is True for r in comparisons),
               'purpose': metadata['purpose']}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('pack', 'images', 'model', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--threshold', type=float, default=.44)
    parser.add_argument('--imgsz', type=int, default=448)
    parser.add_argument('--augment', action=argparse.BooleanOptionalAction, default=True)
    print(json.dumps(run(**vars(parser.parse_args())), indent=2))
