import csv
from pathlib import Path

from importlib.metadata import PackageNotFoundError

import tools.package_model as package_model
from tools.package_model import best_row, installed_version, package


def test_best_row_selects_map50_95_not_last_epoch(tmp_path: Path) -> None:
    path = tmp_path / "results.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("epoch", "metrics/mAP50-95(B)"))
        writer.writeheader(); writer.writerows((
            {"epoch": "0", "metrics/mAP50-95(B)": ".4"},
            {"epoch": "1", "metrics/mAP50-95(B)": ".3"},
        ))
    assert best_row(path)["epoch"] == "0"


def test_installed_version_allows_missing_optional_runtime(monkeypatch) -> None:
    def missing(_package_name: str) -> str:
        raise PackageNotFoundError

    monkeypatch.setattr(package_model, "version", missing)
    assert installed_version("torch") is None


def test_package_uses_final_layout_and_training_config_name(tmp_path: Path) -> None:
    run = tmp_path / "run"; (run / "weights").mkdir(parents=True)
    (run / "weights/best.pt").write_bytes(b"controlled weights")
    (run / "args.yaml").write_text("epochs: 1\n", encoding="utf-8")
    with (run / "results.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ("epoch", "metrics/precision(B)", "metrics/recall(B)", "metrics/mAP50(B)", "metrics/mAP50-95(B)")
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        writer.writerow(dict(zip(fields, ("1", ".5", ".4", ".45", ".3"))))
    dataset = tmp_path / "dataset.json"; dataset.write_text("{}", encoding="utf-8")
    metadata = package(run, tmp_path / "model", tmp_path / "artifacts", dataset, threshold=.35)
    assert metadata["best_epoch"] == 1
    assert (tmp_path / "model/best.pt").is_file()
    assert (tmp_path / "artifacts/training_config.yaml").read_text(encoding="utf-8") == "epochs: 1\n"
