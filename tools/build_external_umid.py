from __future__ import annotations

import argparse
import json
import os
import shutil
from collections import Counter
from pathlib import Path

VECTOR_NAMES = ["eryth", "leuko", "epith", "epithn", "cast", "cryst", "mycete"]
UMID_TO_VECTOR = {0: 1, 1: 0, 2: 2}  # pus->leuko, rbc->eryth, ep->epith


def _link_or_copy(source: Path, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, destination)
        return "hardlink"
    except OSError:
        shutil.copy2(source, destination)
        return "copy"


def remap_line(line: str) -> str:
    parts = line.split()
    if len(parts) != 5:
        raise ValueError(f"Etiqueta YOLO inválida: {line}")
    source_id = int(parts[0])
    if source_id not in UMID_TO_VECTOR:
        raise ValueError(f"Clase UMID desconocida: {source_id}")
    return " ".join((str(UMID_TO_VECTOR[source_id]), *parts[1:]))


def build(source: Path, output: Path) -> dict:
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"El destino debe estar vacío o no existir: {output}")
    image_out, label_out = output / "images" / "test", output / "labels" / "test"
    excluded: list[dict[str, str]] = []
    objects: Counter[str] = Counter()
    materialization: Counter[str] = Counter()
    image_count = 0
    for split in ("train", "val", "test"):
        for image in sorted((source / "images" / split).glob("*")):
            if not image.is_file():
                continue
            label = source / "labels" / split / f"{image.stem}.txt"
            if not label.is_file():
                excluded.append({"source_split": split, "image": image.name, "reason": "missing_annotation"})
                continue
            remapped = []
            for line in label.read_text(encoding="utf-8-sig").splitlines():
                if not line.strip():
                    continue
                mapped = remap_line(line)
                remapped.append(mapped)
                objects[VECTOR_NAMES[int(mapped.split()[0])]] += 1
            destination_name = f"{split}_{image.name}"
            materialization[_link_or_copy(image, image_out / destination_name)] += 1
            label_out.mkdir(parents=True, exist_ok=True)
            (label_out / f"{Path(destination_name).stem}.txt").write_text("\n".join(remapped) + ("\n" if remapped else ""), encoding="utf-8")
            image_count += 1
    yaml = "train: images/test\nval: images/test\ntest: images/test\nnames:\n" + "".join(f"  {index}: {name}\n" for index, name in enumerate(VECTOR_NAMES))
    output.mkdir(parents=True, exist_ok=True)
    (output / "data.yaml").write_text(yaml, encoding="utf-8")
    summary = {"source": "UMID independent external dataset", "images": image_count, "objects": dict(objects), "total_objects": sum(objects.values()), "excluded": excluded, "materialization": dict(materialization), "usage": "external evaluation only; never threshold or model selection"}
    (output / "dataset_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepara UMID como evaluación externa compatible con la ontología VECTOR.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data_processed/UMID_external"))
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.output), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
