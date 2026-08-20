from pathlib import Path
from types import SimpleNamespace

from tools.quality_gate import _fingerprint


def test_quality_gate_fingerprint_is_stable():
    box = SimpleNamespace(x=1, y=2, width=3, height=4)
    detection = SimpleNamespace(class_name="eryth", confidence=.75, bbox=box)
    analysis = SimpleNamespace(detections=[detection])
    assert _fingerprint(analysis) == _fingerprint(analysis)
