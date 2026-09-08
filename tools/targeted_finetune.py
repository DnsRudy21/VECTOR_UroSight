"""Bounded real-data pilot with an exact training manifest and untouched test."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import random


def run(model: Path, dataset: Path, hard_cases: Path, output: Path, epochs: int = 3):
    from ultralytics import YOLO
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    train = sorted((dataset / 'images' / 'train').glob('*.jpg'))
    if not train:
        raise ValueError('No real training images')
    by_name = {p.name: p for p in train}
    with (hard_cases / 'hard_cases_manifest.csv').open(encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    if any(r['original_split'] != 'train' or r['dataset'] != 'USE' for r in rows):
        raise ValueError('Hard cases must come exclusively from USE train')
    # Dense eryth/leuko fields remain review cases, not extra exposures: one
    # field may contain hundreds of RBCs and undo minority-class balancing.
    selected = sorted({Path(r['source_file']).name for r in rows if r['group'] != 'eryth_leuko'})
    hard = [by_name[name] for name in selected]
    sample = random.Random(42).sample(train, min(700, len(train)))
    base = sorted(set(sample) | set(hard))
    # At most two exposures per field; never sample the object-level CSV as images.
    exposures = base + hard
    counts = Counter()
    manifest = []
    for p in exposures:
        label = dataset / 'labels' / 'train' / (p.stem + '.txt')
        counts.update(int(line.split()[0]) for line in label.read_text().splitlines())
        manifest.append({'image': str(p.resolve()), 'label': str(label.resolve()),
                         'image_sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                         'label_sha256': hashlib.sha256(label.read_bytes()).hexdigest(), 'split': 'train'})
    (output / 'training_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    listing = output / 'train.txt'
    listing.write_text('\n'.join(p.resolve().as_posix() for p in exposures)+'\n', encoding='utf-8')
    yaml = output / 'data.yaml'
    yaml.write_text('train: '+listing.resolve().as_posix()+'\nval: '+(dataset/'images'/'val').resolve().as_posix()+
                    '\nnames: [eryth, leuko, epith, epithn, cast, cryst, mycete]\n', encoding='utf-8')
    config = dict(data=str(yaml.resolve()), epochs=epochs, patience=2, seed=42,
                  imgsz=448, batch=4, workers=0, device='cpu', optimizer='AdamW',
                  lr0=.0001, lrf=.1, freeze=10, warmup_epochs=.5,
                  degrees=5., scale=.1, translate=.03, shear=0., perspective=0.,
                  hsv_h=0., hsv_s=0., hsv_v=.1, fliplr=.5, flipud=.5,
                  mosaic=0., mixup=0., copy_paste=0., close_mosaic=0,
                  project=str(output.resolve()), name='run_hardcases_v1', exist_ok=False,
                  plots=False, cache=False, deterministic=True)
    (output/'protocol.json').write_text(json.dumps({'model':str(model.resolve()),
        'model_sha256':hashlib.sha256(model.read_bytes()).hexdigest(), 'config':config,
        'unique_train_fields':len(base), 'exposures':len(exposures), 'hard_fields':len(hard),
        'objects_by_class_id':dict(counts), 'test_used':False,
        'purpose':'bounded pilot: frozen backbone, real training subset plus one extra hard-case exposure'},indent=2),encoding='utf-8')
    YOLO(str(model)).train(**config)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('model','dataset','hard_cases','output'):
        parser.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    parser.add_argument('--epochs',type=int,default=3)
    run(**vars(parser.parse_args()))
