"""Select reproducible training-only review candidates, without editing sources."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

from tools.error_analysis import yolo_truth
from PIL import Image


def mine(source: Path, dataset: Path, output: Path, limit: int = 20) -> dict:
    if output.exists():
        raise FileExistsError(output)
    candidates = defaultdict(list)
    for image in sorted((dataset / 'images' / 'train').glob('*.jpg')):
        with Image.open(image) as im:
            width, height = im.size
        truth = yolo_truth(dataset / 'labels' / 'train' / (image.stem + '.txt'), width, height)
        classes = Counter(t['class_id'] for t in truth)
        for class_id, group in ((4, 'cast'), (6, 'mycete'), (3, 'epithn'), (5, 'cryst')):
            targets = [t for t in truth if t['class_id'] == class_id]
            if targets:
                min_area = min((t['box'][2]-t['box'][0])*(t['box'][3]-t['box'][1])/(width*height) for t in targets)
                candidates[group].append((min_area, image, 'small annotated object; size/contrast review', class_id))
        if classes[0] and classes[1]:
            candidates['eryth_leuko'].append((-classes[0]-classes[1], image, 'dense field with both annotated classes', None))
    rows = []
    for group in ('cast', 'mycete', 'epithn', 'eryth_leuko', 'cryst'):
        folder = output / group; folder.mkdir(parents=True)
        ordered = sorted(candidates[group], key=lambda x: (x[0], x[1].name))
        # Include both small and large morphology, without duplicating a field within its group.
        selected = ordered[:limit] if group == 'eryth_leuko' else ordered[:limit//2] + list(reversed(ordered[limit//2:]))[:limit-limit//2]
        for score, image, reason, class_id in selected:
            xml = source / 'Annotations' / (image.stem + '.xml')
            shutil.copy2(image, folder / image.name); shutil.copy2(xml, folder / xml.name)
            shutil.copy2(dataset / 'labels' / 'train' / (image.stem + '.txt'), folder / (image.stem + '.txt'))
            names = ['eryth','leuko','epith','epithn','cast','cryst','mycete']
            for index, obj in enumerate(ET.parse(xml).getroot().findall('object')):
                name = obj.findtext('name')
                if name not in (['eryth','leuko'] if class_id is None else [names[class_id]]):
                    continue
                rows.append({'source_file': str((source / 'JPEGImages' / image.name).resolve()),
                             'dataset': 'USE', 'annotation': str(xml.resolve()), 'object_index': index,
                             'class': name, 'bbox_xyxy': json.dumps([float(obj.findtext('bndbox/'+k)) for k in ('xmin','ymin','xmax','ymax')]),
                             'original_split': 'train', 'group': group,
                             'selection_reason': reason if group == 'eryth_leuko' else 'annotated size extremes; morphology review candidate',
                             'ranking_value': score, 'image_sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                             'annotation_sha256': hashlib.sha256(xml.read_bytes()).hexdigest(),
                             'copied_image': str((folder / image.name).resolve()),
                             'review_status': 'technical_selection_not_expert_verified'})
    with (output / 'hard_cases_manifest.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    summary = {'usage': 'train-only review candidates; no clinical relabeling',
               'selected_fields_by_group': {g: len({r['source_file'] for r in rows if r['group'] == g}) for g in candidates},
               'objects': len(rows), 'test_used': False, 'source_modified': False}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'dataset', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--limit', type=int, default=20)
    print(mine(**vars(parser.parse_args())))
