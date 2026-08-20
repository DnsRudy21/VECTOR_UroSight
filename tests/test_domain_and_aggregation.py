from pathlib import Path

import pytest

from src.domain.models import BoundingBox, Detection, ImageAnalysis, StudyResult
from src.processing.aggregator import normalize_study


def test_study_metrics_ignore_failed_images():
    detection = Detection("rbc", 0.8, BoundingBox(10, 10, 5, 5))
    result = normalize_study(StudyResult([
        ImageAnalysis(Path("one.png"), [detection], 12.5),
        ImageAnalysis(Path("bad.png"), error="failed"),
    ]))
    assert result.class_counts() == {"eritrocitos": 1}
    assert result.averages_per_image() == {"eritrocitos": 1.0}
    assert result.average_confidence() == pytest.approx(0.8)
    assert result.total_inference_ms() == pytest.approx(12.5)
