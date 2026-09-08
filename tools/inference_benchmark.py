"""Warm operational CPU benchmark, after training/evaluation processes finish."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import random
import time

from tools.validation_experiments import transform_image


def run(model: Path, images: Path, output: Path):
    import cv2
    import psutil
    from ultralytics import YOLO
    available = sorted(images.glob('*.jpg'))
    paths = random.Random(42).sample(available, min(16, len(available)))
    if not paths or output.exists():
        raise ValueError('Require images and a new output file')
    detector = YOLO(str(model))
    rows = []
    for variant in ('original448', 'original640', 'clahe', 'contrast', 'brightness', 'denoise'):
        size = 640 if variant == 'original640' else 448
        detector.predict(transform_image(cv2.imread(str(paths[0])), variant), imgsz=size,
                         conf=.44, augment=True, device='cpu', verbose=False)
        samples = []; memory = 0
        for _ in range(3):
            for path in paths:
                start = time.perf_counter()
                detector.predict(transform_image(cv2.imread(str(path)), variant), imgsz=size,
                                 conf=.44, augment=True, device='cpu', verbose=False)
                samples.append((time.perf_counter()-start)*1000)
                memory = max(memory, psutil.Process().memory_info().rss)
        rows.append({'variant':variant,'median_ms':statistics.median(samples),
                     'mean_ms':statistics.mean(samples),'max_ms':max(samples),
                     'sampled_rss_bytes':memory,'samples':samples})
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps({'model_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),
        'images':[str(p.resolve()) for p in paths], 'seed':42, 'rounds':3,'threshold':.44,'augment':True,
        'scope':'16 validation images; warm latency including read/preprocess/predict; excludes matching',
        'memory_scope':'sampled shared-process RSS including retained allocator buffers, not isolated model size',
        'results':rows},indent=2),encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('model','images','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    run(**vars(parser.parse_args()))
