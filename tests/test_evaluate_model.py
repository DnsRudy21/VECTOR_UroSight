import json
from pathlib import Path
from types import SimpleNamespace

from tools.evaluate_model import metrics_payload, write_evaluation


def test_metrics_payload_and_files_are_machine_readable(tmp_path: Path) -> None:
    box = SimpleNamespace(mp=.7, mr=.6, map50=.65, map=.4, maps=[.3, .5], p=[.8, .6], r=[.5, .7], ap50=[.6, .7])
    metrics = SimpleNamespace(box=box, fitness=.425, speed={"inference": 12.5}, nt_per_class=[10, 20])
    summary, rows = metrics_payload(metrics, {0: "eryth", 1: "leuko"}, split="test", confidence=None)
    write_evaluation(tmp_path, summary, rows)
    persisted = json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8"))
    assert persisted["map50"] == .65
    assert persisted["split"] == "test"
    assert rows[1]["class_name"] == "leuko"
    assert rows[1]["support"] == 20
    assert (tmp_path / "metrics_by_class.csv").read_text(encoding="utf-8-sig").splitlines()[0].startswith("class_id")


def test_metrics_payload_handles_classes_absent_from_external_dataset() -> None:
    box = SimpleNamespace(mp=.6, mr=.5, map50=.55, map=.3, maps=[.3, .4, .2, 0], p=[.7, .5], r=[.6, .4], ap50=[.65, .45], ap_class_index=[0, 2])
    metrics = SimpleNamespace(box=box, fitness=.3, speed={}, nt_per_class=[5, 0, 7, 0])
    _, rows = metrics_payload(metrics, {0: "eryth", 1: "leuko", 2: "epith", 3: "cast"}, split="test", confidence=.35)
    assert rows[1]["support"] == 0 and rows[1]["precision"] == 0
    assert rows[2]["support"] == 7 and rows[2]["precision"] == .5
