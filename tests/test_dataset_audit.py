from pathlib import Path

from PIL import Image

from tools.dataset_audit import audit_voc, audit_yolo


def _image(path: Path, color: str = "white") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (20, 10), color).save(path)


def test_audit_yolo_reports_missing_label_and_split_leak(tmp_path: Path) -> None:
    root, out = tmp_path / "yolo", tmp_path / "out"
    for split in ("train", "val", "test"):
        (root / "labels" / split).mkdir(parents=True)
        (root / "images" / split).mkdir(parents=True)
    _image(root / "images/train/a.jpg")
    _image(root / "images/val/b.jpg")
    _image(root / "images/test/c.jpg", "black")
    (root / "labels/train/a.txt").write_text("1 0.5 0.5 0.2 0.2\n", encoding="utf-8")
    (root / "labels/test/c.txt").write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")

    summary = audit_yolo(root, out, ["pus", "rbc", "ep"])

    assert summary["annotation_object_count"] == 2
    assert summary["issues"]["missing_annotation"] == 1
    assert summary["issues"]["exact_duplicate_across_splits"] == 1
    assert not any(str(tmp_path) in file.read_text(encoding="utf-8-sig") for file in out.glob("*.csv"))


def test_audit_voc_validates_bbox(tmp_path: Path) -> None:
    root, out = tmp_path / "voc", tmp_path / "out"
    _image(root / "JPEGImages/a.jpg")
    (root / "Annotations").mkdir()
    (root / "ImageSets/Main").mkdir(parents=True)
    for split, content in (("train", "a\n"), ("val", ""), ("test", "")):
        (root / f"ImageSets/Main/{split}.txt").write_text(content, encoding="utf-8")
    (root / "Annotations/a.xml").write_text("<annotation><size><width>20</width><height>10</height></size><object><name>eryth</name><bndbox><xmin>1</xmin><ymin>1</ymin><xmax>25</xmax><ymax>8</ymax></bndbox></object></annotation>", encoding="utf-8")

    summary = audit_voc(root, out)

    assert summary["annotation_object_count"] == 1
    assert summary["valid_object_count"] == 0
    assert summary["issues"]["invalid_bbox"] == 1
