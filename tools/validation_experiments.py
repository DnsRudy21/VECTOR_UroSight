"""Fixed-threshold, per-class validation experiments; test is not selectable."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from tools.error_analysis import match_detections, yolo_truth

THRESHOLDS = (.15, .20, .25, .30, .35, .40, .44, .50)


def transform_image(image, variant):
    import cv2
    if variant == 'clahe':
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        lab[:, :, 0] = cv2.createCLAHE(clipLimit=2., tileGridSize=(8, 8)).apply(lab[:, :, 0])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    if variant == 'contrast':
        return np.clip((image.astype(float) - 127.5) * 1.05 + 127.5, 0, 255).astype('uint8')
    if variant == 'brightness':
        return np.clip(image.astype(float) + 3, 0, 255).astype('uint8')
    if variant == 'denoise':
        return cv2.bilateralFilter(image, 5, 25, 25)
    return image


def counts(truth, predictions):
    matched = match_detections(truth, predictions)
    result = np.zeros((7, 3), dtype=int)  # TP, FP, FN; confusion counts on both sides
    for ti, _ in matched['true_positives']:
        result[truth[ti]['class_id'], 0] += 1
    for pi in matched['false_positives']:
        result[predictions[pi]['class_id'], 1] += 1
    for ti in matched['false_negatives']:
        result[truth[ti]['class_id'], 2] += 1
    for ti, pi in matched['misclassifications']:
        result[truth[ti]['class_id'], 2] += 1
        result[predictions[pi]['class_id'], 1] += 1
    return result


def run(model_path, dataset, output, variants):
    import cv2
    import psutil
    from ultralytics import YOLO
    if output.exists():
        raise FileExistsError(output)
    images = sorted((dataset / 'images' / 'val').glob('*.jpg'))
    if not images or any(not (dataset / 'labels' / 'val' / (p.stem + '.txt')).is_file() for p in images):
        raise ValueError('Complete real validation images and annotations required')
    output.mkdir(parents=True)
    model = YOLO(str(model_path))
    metadata = {'split': 'val', 'model_sha256': hashlib.sha256(model_path.read_bytes()).hexdigest(),
                'data': str(dataset.resolve()), 'images': len(images), 'thresholds': THRESHOLDS,
                'iou': .5, 'augment': True, 'seed': 42,
                'matching': 'class-aware greedy IoU; confusion is FP and FN',
                'memory': 'sampled process RSS; not instantaneous peak',
                'variants': variants, 'selection': 'validation only; no clinical claims'}
    (output / 'experiment.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    all_rows = []
    for variant in variants:
        totals = {t: np.zeros((7, 3), dtype=int) for t in THRESHOLDS}
        elapsed = 0.; memory = 0
        size = 640 if variant == 'original640' else 448
        with (output / (variant + '.jsonl')).open('w', encoding='utf-8') as stream:
            for index, path in enumerate(images):
                start = time.perf_counter()
                image = cv2.imread(str(path)); height, width = image.shape[:2]
                truth = yolo_truth(dataset / 'labels' / 'val' / (path.stem + '.txt'), width, height)
                image = transform_image(image, variant)
                result = model.predict(image, imgsz=size, conf=.15, augment=True, device='cpu', verbose=False)[0]
                predictions = [{'class_id': int(b.cls.item()), 'box': b.xyxy[0].tolist(),
                                'confidence': float(b.conf.item())} for b in result.boxes]
                duration = time.perf_counter() - start; elapsed += duration
                memory = max(memory, psutil.Process().memory_info().rss)
                for threshold in THRESHOLDS:
                    totals[threshold] += counts(truth, [p for p in predictions if p['confidence'] >= threshold])
                stream.write(json.dumps({'image': path.name, 'predictions': predictions, 'wall_seconds': duration}) + '\n')
                if (index + 1) % 100 == 0:
                    stream.flush(); print(variant, index + 1, '/', len(images), flush=True)
        for threshold, values in totals.items():
            for class_id, (tp, fp, fn) in enumerate(values):
                precision = tp / (tp + fp) if tp + fp else 0.
                recall = tp / (tp + fn) if tp + fn else 0.
                all_rows.append({'variant': variant, 'imgsz': size, 'threshold': threshold,
                                 'class': model.names[class_id], 'tp': int(tp), 'fp': int(fp), 'fn': int(fn),
                                 'detections': int(tp + fp), 'precision': precision, 'recall': recall,
                                 'f1': 2 * precision * recall / (precision + recall) if precision + recall else 0.,
                                 'wall_ms_per_image': elapsed * 1000 / len(images), 'sampled_rss_bytes': memory})
        with (output / 'per_class.csv').open('w', newline='', encoding='utf-8-sig') as stream:
            writer = csv.DictWriter(stream, fieldnames=all_rows[0].keys()); writer.writeheader(); writer.writerows(all_rows)
        print('Completed', variant, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-path', type=Path, required=True)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--variants', nargs='+', choices=['original448', 'original640', 'clahe', 'contrast', 'brightness', 'denoise'],
                        default=['original448', 'original640', 'clahe', 'contrast', 'brightness', 'denoise'])
    run(**vars(parser.parse_args()))
