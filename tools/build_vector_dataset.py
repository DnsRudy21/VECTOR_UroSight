from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

CLASS_NAMES = ["eryth", "leuko", "epith", "epithn", "cast", "cryst", "mycete"]
SPLIT_PRIORITY = {"train": 0, "val": 1, "test": 2}


def _load_images(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def select_records(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    eligible = [row for row in rows if row["splits"] in SPLIT_PRIORITY and row["readable"].lower() == "true"]
    by_hash: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in eligible:
        by_hash[row["sha256"] or f"stem:{row['stem']}"] .append(row)
    selected: list[dict[str, str]] = []
    exclusions: list[dict[str, str]] = []
    for digest, group in sorted(by_hash.items()):
        ordered = sorted(group, key=lambda row: (-SPLIT_PRIORITY[row["splits"]], row["stem"]))
        keeper = ordered[0]
        selected.append(keeper)
        for duplicate in ordered[1:]:
            exclusions.append({"stem": duplicate["stem"], "split": duplicate["splits"], "reason": "exact_duplicate", "kept_stem": keeper["stem"], "kept_split": keeper["splits"], "sha256": digest})
    unreadable = [row for row in rows if row["splits"] in SPLIT_PRIORITY and row["readable"].lower() != "true"]
    exclusions.extend({"stem": row["stem"], "split": row["splits"], "reason": "unreadable_image", "kept_stem": "", "kept_split": "", "sha256": row["sha256"]} for row in unreadable)
    return selected, exclusions


def _link_or_copy(source: Path, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, destination)
        return "hardlink"
    except OSError:
        shutil.copy2(source, destination)
        return "copy"


def _convert_xml(xml_path: Path, width: int, height: int) -> tuple[list[str], list[dict], Counter[str]]:
    root = ET.parse(xml_path).getroot()
    labels: list[str] = []
    corrections: list[dict] = []
    counts: Counter[str] = Counter()
    for index, node in enumerate(root.findall("object")):
        raw_class = (node.findtext("name") or "").strip()
        if raw_class not in CLASS_NAMES:
            corrections.append({"annotation": xml_path.name, "object": index, "action": "discard_unknown_class", "details": raw_class})
            continue
        box = node.find("bndbox")
        original = [float(box.findtext(key)) for key in ("xmin", "ymin", "xmax", "ymax")]
        xmin, ymin = max(0.0, original[0]), max(0.0, original[1])
        xmax, ymax = min(float(width), original[2]), min(float(height), original[3])
        if [xmin, ymin, xmax, ymax] != original:
            corrections.append({"annotation": xml_path.name, "object": index, "action": "clip_to_image", "details": json.dumps({"original": original, "clipped": [xmin, ymin, xmax, ymax]})})
        if xmax <= xmin or ymax <= ymin:
            corrections.append({"annotation": xml_path.name, "object": index, "action": "discard_zero_area", "details": str([xmin, ymin, xmax, ymax])})
            continue
        x_center = ((xmin + xmax) / 2) / width
        y_center = ((ymin + ymax) / 2) / height
        box_width = (xmax - xmin) / width
        box_height = (ymax - ymin) / height
        labels.append(f"{CLASS_NAMES.index(raw_class)} {x_center:.8f} {y_center:.8f} {box_width:.8f} {box_height:.8f}")
        counts[raw_class] += 1
    return labels, corrections, counts


def build(source_root: Path, audit_root: Path, output_root: Path) -> dict:
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"El destino debe estar vacío o no existir: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    selected, exclusions = select_records(_load_images(audit_root / "images.csv"))
    corrections: list[dict] = []
    counts: Counter[str] = Counter()
    split_counts: Counter[str] = Counter()
    materialization: Counter[str] = Counter()
    for row in selected:
        split, stem = row["splits"], row["stem"]
        source_image = source_root / row["image"]
        destination_image = output_root / "images" / split / source_image.name
        materialization[_link_or_copy(source_image, destination_image)] += 1
        labels, changes, class_counts = _convert_xml(source_root / "Annotations" / f"{stem}.xml", int(row["width"]), int(row["height"]))
        label_path = output_root / "labels" / split / f"{stem}.txt"
        label_path.parent.mkdir(parents=True, exist_ok=True)
        label_path.write_text("\n".join(labels) + ("\n" if labels else ""), encoding="utf-8")
        corrections.extend(changes)
        counts.update(class_counts)
        split_counts[split] += 1
    yaml = "train: images/train\nval: images/val\ntest: images/test\nnames:\n" + "".join(f"  {index}: {name}\n" for index, name in enumerate(CLASS_NAMES))
    (output_root / "data.yaml").write_text(yaml, encoding="utf-8")
    with (output_root / "exclusions.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=("stem", "split", "reason", "kept_stem", "kept_split", "sha256")); writer.writeheader(); writer.writerows(exclusions)
    with (output_root / "corrections.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=("annotation", "object", "action", "details")); writer.writeheader(); writer.writerows(corrections)
    summary = {"source": "USE", "class_names": CLASS_NAMES, "images": dict(split_counts), "total_images": sum(split_counts.values()), "objects": dict(counts), "total_objects": sum(counts.values()), "excluded_images": len(exclusions), "recorded_corrections": len(corrections), "materialization": dict(materialization), "split_policy": "Preserve inherited split unless duplicate; prefer test, then val, then train; keep one exact image."}
    (output_root / "dataset_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    (output_root / "conversion_report.json").write_text(json.dumps({"exclusions": exclusions, "corrections": corrections}, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Construye el dataset maestro YOLO deduplicado a partir de USE.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data_processed/VECTOR_dataset"))
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.audit, args.output), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
