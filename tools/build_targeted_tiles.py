from __future__ import annotations

import argparse
import json
import os
import shutil
from collections import Counter
from pathlib import Path

from PIL import Image

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
DEFAULT_TARGETS = {3, 5, 6}  # epithn, cryst, mycete


def _materialize(source: Path, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, destination)
        return "hardlink"
    except OSError:
        shutil.copy2(source, destination)
        return "copy"


def _read_labels(path: Path, width: int, height: int) -> list[tuple[int, float, float, float, float]]:
    labels = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        class_id, xc, yc, box_width, box_height = line.split()
        labels.append((int(class_id), float(xc) * width, float(yc) * height,
                       float(box_width) * width, float(box_height) * height))
    return labels


def crop_labels(
    labels: list[tuple[int, float, float, float, float]],
    crop: tuple[int, int, int, int],
    *,
    minimum_visible: float = 0.5,
) -> list[str]:
    """Transform YOLO pixel labels into one crop, retaining sufficiently visible boxes."""
    left, top, right, bottom = crop
    crop_width, crop_height = right - left, bottom - top
    transformed: list[str] = []
    for class_id, xc, yc, width, height in labels:
        x1, y1, x2, y2 = xc - width / 2, yc - height / 2, xc + width / 2, yc + height / 2
        clipped = max(left, x1), max(top, y1), min(right, x2), min(bottom, y2)
        visible_width, visible_height = clipped[2] - clipped[0], clipped[3] - clipped[1]
        if visible_width <= 0 or visible_height <= 0:
            continue
        if (visible_width * visible_height) / (width * height) < minimum_visible:
            continue
        new_xc = ((clipped[0] + clipped[2]) / 2 - left) / crop_width
        new_yc = ((clipped[1] + clipped[3]) / 2 - top) / crop_height
        new_width, new_height = visible_width / crop_width, visible_height / crop_height
        transformed.append(
            f"{class_id} {new_xc:.8f} {new_yc:.8f} {new_width:.8f} {new_height:.8f}"
        )
    return transformed


def _crop_window(xc: float, yc: float, width: int, height: int, size: int) -> tuple[int, int, int, int]:
    size = min(size, width, height)
    left = min(max(0, round(xc - size / 2)), width - size)
    top = min(max(0, round(yc - size / 2)), height - size)
    return left, top, left + size, top + size


def build(base: Path, output: Path, *, tile_size: int = 512, max_tiles_per_image: int = 2,
          target_classes: set[int] | None = None) -> dict:
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"El destino debe estar vacío o no existir: {output}")
    targets = DEFAULT_TARGETS if target_classes is None else target_classes
    materialization: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    tile_classes: Counter[int] = Counter()
    tiles = 0

    for split in ("train", "val", "test"):
        for source_image in sorted((base / "images" / split).iterdir()):
            if not source_image.is_file() or source_image.suffix.lower() not in IMAGE_SUFFIXES:
                continue
            materialization[_materialize(source_image, output / "images" / split / source_image.name)] += 1
            source_label = base / "labels" / split / f"{source_image.stem}.txt"
            _materialize(source_label, output / "labels" / split / source_label.name)
            source_counts[split] += 1
            if split != "train":
                continue
            with Image.open(source_image) as image:
                image = image.convert("RGB")
                labels = _read_labels(source_label, *image.size)
                anchors = sorted(
                    (label for label in labels if label[0] in targets),
                    key=lambda label: (label[0], label[1], label[2]),
                )
                windows: list[tuple[int, int, int, int]] = []
                for anchor in anchors:
                    window = _crop_window(anchor[1], anchor[2], *image.size, tile_size)
                    if window in windows:
                        continue
                    windows.append(window)
                    if len(windows) >= max_tiles_per_image:
                        break
                for index, window in enumerate(windows, 1):
                    transformed = crop_labels(labels, window)
                    if not transformed:
                        continue
                    name = f"{source_image.stem}__target_{index:02d}"
                    image.crop(window).save(output / "images" / "train" / f"{name}.jpg", quality=95)
                    (output / "labels" / "train" / f"{name}.txt").write_text(
                        "\n".join(transformed) + "\n", encoding="utf-8"
                    )
                    tile_classes.update(int(line.split()[0]) for line in transformed)
                    tiles += 1

    source_yaml = (base / "data.yaml").read_text(encoding="utf-8")
    (output / "data.yaml").write_text(source_yaml, encoding="utf-8")
    summary = {
        "strategy": "original training images plus deterministic target-centered tiles; validation and test unchanged",
        "source_dataset": str(base.resolve()),
        "source_images": dict(source_counts),
        "generated_train_tiles": tiles,
        "result_images": {**source_counts, "train": source_counts["train"] + tiles},
        "tile_size": tile_size,
        "max_tiles_per_image": max_tiles_per_image,
        "target_class_ids": sorted(targets),
        "objects_in_tiles_by_class_id": dict(sorted(tile_classes.items())),
        "materialization": dict(materialization),
        "test_used_for_training_or_selection": False,
    }
    (output / "targeted_tiles_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Crea tiles de entrenamiento dirigidos sin alterar validation/test.")
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tile-size", type=int, default=512)
    parser.add_argument("--max-tiles-per-image", type=int, default=2)
    args = parser.parse_args()
    print(json.dumps(build(args.base, args.output, tile_size=args.tile_size,
                           max_tiles_per_image=args.max_tiles_per_image), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
