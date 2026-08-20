from __future__ import annotations

import argparse
import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


@dataclass(frozen=True)
class AuditPaths:
    source_root: Path
    output_root: Path


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _write_csv(path: Path, rows: list[dict], fields: Iterable[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields))
        writer.writeheader()
        writer.writerows(rows)


def _image_metadata(path: Path) -> tuple[int | None, int | None, str | None]:
    try:
        with Image.open(path) as image:
            width, height = image.size
            image.verify()
        return width, height, None
    except Exception as exc:  # Pillow exposes several decoder-specific exceptions.
        return None, None, f"{type(exc).__name__}: {exc}"


def _split_members(directory: Path) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for split in ("train", "val", "test"):
        manifest = directory / f"{split}.txt"
        result[split] = {
            line.strip() for line in manifest.read_text(encoding="utf-8-sig").splitlines() if line.strip()
        }
    return result


def audit_voc(source_root: Path, output_root: Path, *, hash_images: bool = True) -> dict:
    annotations = source_root / "Annotations"
    images_dir = source_root / "JPEGImages"
    split_dir = source_root / "ImageSets" / "Main"
    splits = _split_members(split_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    issues: list[dict] = []
    objects: list[dict] = []
    images: list[dict] = []
    classes: Counter[str] = Counter()
    hash_splits: defaultdict[str, set[str]] = defaultdict(set)

    membership: defaultdict[str, list[str]] = defaultdict(list)
    for split, stems in splits.items():
        for stem in stems:
            membership[stem].append(split)
    for stem, assigned in membership.items():
        if len(assigned) > 1:
            issues.append({"issue_type": "stem_in_multiple_splits", "item": stem, "details": ",".join(assigned)})

    image_by_stem = {p.stem: p for p in images_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES}
    xml_by_stem = {p.stem: p for p in annotations.glob("*.xml")}
    for stem in sorted(set(image_by_stem) | set(xml_by_stem) | set(membership)):
        image_path = image_by_stem.get(stem)
        xml_path = xml_by_stem.get(stem)
        assigned = membership.get(stem, [])
        if image_path is None:
            issues.append({"issue_type": "missing_image", "item": stem, "details": ",".join(assigned)})
            continue
        if xml_path is None:
            issues.append({"issue_type": "missing_annotation", "item": _relative(image_path, source_root), "details": ""})
        if not assigned:
            issues.append({"issue_type": "image_outside_splits", "item": _relative(image_path, source_root), "details": ""})

        width, height, image_error = _image_metadata(image_path)
        digest = _digest(image_path) if hash_images and image_error is None else ""
        for split in assigned:
            if digest:
                hash_splits[digest].add(split)
        images.append({
            "image": _relative(image_path, source_root), "stem": stem, "splits": ",".join(assigned),
            "width": width, "height": height, "sha256": digest, "readable": image_error is None,
        })
        if image_error:
            issues.append({"issue_type": "unreadable_image", "item": _relative(image_path, source_root), "details": image_error})
        if xml_path is None:
            continue
        try:
            root = ET.parse(xml_path).getroot()
        except (ET.ParseError, OSError) as exc:
            issues.append({"issue_type": "invalid_xml", "item": _relative(xml_path, source_root), "details": str(exc)})
            continue
        declared_w = int(float(root.findtext("size/width", "0")))
        declared_h = int(float(root.findtext("size/height", "0")))
        if width and height and (declared_w, declared_h) != (width, height):
            issues.append({"issue_type": "dimension_mismatch", "item": _relative(xml_path, source_root), "details": f"xml={declared_w}x{declared_h}; image={width}x{height}"})
        for index, node in enumerate(root.findall("object")):
            raw_class = (node.findtext("name") or "").strip()
            box = node.find("bndbox")
            values: list[float | None] = []
            for key in ("xmin", "ymin", "xmax", "ymax"):
                try:
                    values.append(float(box.findtext(key)) if box is not None else None)
                except (TypeError, ValueError):
                    values.append(None)
            valid = (
                all(value is not None for value in values)
                and values[0] >= 0 and values[1] >= 0
                and values[2] > values[0] and values[3] > values[1]
                and values[2] <= declared_w and values[3] <= declared_h
            )
            if not raw_class:
                valid = False
            if not valid:
                issues.append({"issue_type": "invalid_bbox", "item": _relative(xml_path, source_root), "details": f"object={index}; class={raw_class}; box={values}"})
            classes[raw_class or "__missing__"] += 1
            objects.append({"annotation": _relative(xml_path, source_root), "stem": stem, "split": assigned[0] if len(assigned) == 1 else "", "class": raw_class, "xmin": values[0], "ymin": values[1], "xmax": values[2], "ymax": values[3], "valid": valid})

    for digest, assigned in hash_splits.items():
        if len(assigned) > 1:
            issues.append({"issue_type": "exact_duplicate_across_splits", "item": digest, "details": ",".join(sorted(assigned))})
    return _persist(output_root, "USE", splits, images, objects, classes, issues)


def audit_yolo(source_root: Path, output_root: Path, names: list[str], *, hash_images: bool = True) -> dict:
    output_root.mkdir(parents=True, exist_ok=True)
    issues: list[dict] = []
    objects: list[dict] = []
    images: list[dict] = []
    classes: Counter[str] = Counter()
    splits: dict[str, set[str]] = {}
    hash_splits: defaultdict[str, set[str]] = defaultdict(set)
    for split in ("train", "val", "test"):
        image_dir, label_dir = source_root / "images" / split, source_root / "labels" / split
        image_files = {p.stem: p for p in image_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES}
        label_files = {p.stem: p for p in label_dir.glob("*.txt")}
        splits[split] = set(image_files)
        for stem in sorted(set(image_files) | set(label_files)):
            image_path, label_path = image_files.get(stem), label_files.get(stem)
            if image_path is None:
                issues.append({"issue_type": "label_without_image", "item": _relative(label_path, source_root), "details": split})
                continue
            width, height, image_error = _image_metadata(image_path)
            digest = _digest(image_path) if hash_images and image_error is None else ""
            if digest:
                hash_splits[digest].add(split)
            images.append({"image": _relative(image_path, source_root), "stem": stem, "splits": split, "width": width, "height": height, "sha256": digest, "readable": image_error is None})
            if image_error:
                issues.append({"issue_type": "unreadable_image", "item": _relative(image_path, source_root), "details": image_error})
            if label_path is None:
                issues.append({"issue_type": "missing_annotation", "item": _relative(image_path, source_root), "details": split})
                continue
            for index, line in enumerate(label_path.read_text(encoding="utf-8-sig").splitlines(), 1):
                parts = line.split()
                try:
                    class_id = int(parts[0]); coords = [float(v) for v in parts[1:]]
                except (IndexError, ValueError):
                    class_id, coords = -1, []
                valid = len(coords) == 4 and 0 <= class_id < len(names) and all(0 <= v <= 1 for v in coords) and coords[2] > 0 and coords[3] > 0
                raw_class = names[class_id] if 0 <= class_id < len(names) else "__invalid__"
                classes[raw_class] += 1
                if not valid:
                    issues.append({"issue_type": "invalid_yolo_label", "item": _relative(label_path, source_root), "details": f"line={index}; value={line}"})
                objects.append({"annotation": _relative(label_path, source_root), "stem": stem, "split": split, "class": raw_class, "class_id": class_id, "x_center": coords[0] if len(coords) == 4 else None, "y_center": coords[1] if len(coords) == 4 else None, "width": coords[2] if len(coords) == 4 else None, "height": coords[3] if len(coords) == 4 else None, "valid": valid})
    for digest, assigned in hash_splits.items():
        if len(assigned) > 1:
            issues.append({"issue_type": "exact_duplicate_across_splits", "item": digest, "details": ",".join(sorted(assigned))})
    return _persist(output_root, "UMID", splits, images, objects, classes, issues)


def _persist(output_root: Path, source: str, splits: dict[str, set[str]], images: list[dict], objects: list[dict], classes: Counter[str], issues: list[dict]) -> dict:
    issue_counts = Counter(row["issue_type"] for row in issues)
    summary = {"source": source, "image_count": len(images), "annotation_object_count": len(objects), "valid_object_count": sum(str(row["valid"]).lower() == "true" for row in objects), "classes": dict(classes), "splits": {key: len(value) for key, value in splits.items()}, "issues": dict(issue_counts)}
    (output_root / "dataset_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_csv(output_root / "classes.csv", [{"class": key, "objects": value} for key, value in classes.most_common()], ("class", "objects"))
    _write_csv(output_root / "issues.csv", issues, ("issue_type", "item", "details"))
    _write_csv(output_root / "images.csv", images, images[0].keys() if images else ("image",))
    _write_csv(output_root / "objects.csv", objects, objects[0].keys() if objects else ("annotation",))
    (output_root / "split_manifest.json").write_text(json.dumps({key: sorted(value) for key, value in splits.items()}, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Audita USE (VOC) y UMID (YOLO) sin modificar las fuentes.")
    parser.add_argument("--use-root", type=Path, required=True)
    parser.add_argument("--umid-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts/dataset_audit"))
    parser.add_argument("--no-hash", action="store_true")
    args = parser.parse_args()
    use = audit_voc(args.use_root, args.output / "USE", hash_images=not args.no_hash)
    umid = audit_yolo(args.umid_root, args.output / "UMID", ["pus", "rbc", "ep"], hash_images=not args.no_hash)
    print(json.dumps({"USE": use, "UMID": umid}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
