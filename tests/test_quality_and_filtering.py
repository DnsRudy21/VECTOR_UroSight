from pathlib import Path

from PIL import Image

from src.domain.models import BoundingBox, Detection, ImageAnalysis, ImageQuality, StudyResult
from src.processing.aggregator import normalize_study
from src.processing.image_quality import assess_image_quality


def test_quality_flags_dark_low_contrast_image(tmp_path):
    path = tmp_path / "dark.png"; Image.new("RGB", (320, 200), (10, 10, 10)).save(path)
    quality = assess_image_quality(path)
    assert (quality.width, quality.height) == (320, 200)
    assert "Brillo muy bajo" in quality.warnings
    assert "Contraste insuficiente" in quality.warnings


def test_threshold_updates_all_study_metrics_without_losing_detections():
    detections = [Detection("RBC", .9, BoundingBox(50, 50, 20, 20)),
                  Detection("eryth", .4, BoundingBox(100, 100, 20, 20))]
    result = normalize_study(StudyResult([ImageAnalysis(Path("field.png"), detections,
        quality=ImageQuality(200, 200, 100, 30, 100))], confidence_threshold=.5))
    assert result.class_counts() == {"eritrocitos": 1}
    assert result.hidden_count() == 1
    assert len(result.images[0].raw_detections) == 2
    result.confidence_threshold = .3
    assert result.class_counts() == {"eritrocitos": 2}


def test_nms_removes_equivalent_overlapping_boxes_and_marks_clipping():
    detections = [Detection("RBC", .9, BoundingBox(10, 10, 30, 30)),
                  Detection("eryth", .8, BoundingBox(10, 10, 30, 30))]
    result = normalize_study(StudyResult([ImageAnalysis(Path("field.png"), detections,
        quality=ImageQuality(100, 100, 100, 30, 100))]))
    assert len(result.images[0].detections) == 1
    assert result.images[0].detections[0].requires_review
    assert "duplicada" in result.images[0].warnings[0]
