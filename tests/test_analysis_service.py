from pathlib import Path

from PIL import Image

from src.inference.mock_provider import MockInferenceProvider
from src.services.analysis_service import AnalysisService


def make_image(path: Path) -> Path:
    Image.new("RGB", (640, 480), "white").save(path)
    return path


def test_validation_rejects_corrupt_and_unsupported_files(tmp_path):
    service = AnalysisService(MockInferenceProvider())
    valid = make_image(tmp_path / "válida con espacios.png")
    corrupt = tmp_path / "corrupt.jpg"; corrupt.write_text("not an image")
    unsupported = tmp_path / "note.txt"; unsupported.write_text("text")
    assert service.validate_image(valid)[0]
    assert not service.validate_image(corrupt)[0]
    assert not service.validate_image(unsupported)[0]


def test_analysis_reports_progress_and_normalizes(tmp_path):
    service = AnalysisService(MockInferenceProvider())
    paths = [make_image(tmp_path / f"field-{i}.png") for i in range(2)]
    progress = []
    result = service.analyze(paths, lambda done, total, path: progress.append((done, total, path)))
    assert len(result.successful_images) == 2
    assert progress[-1][:2] == (2, 2)
    assert set(result.class_counts()) <= {"eritrocitos", "leucocitos", "celulas_epiteliales"}


def test_empty_selection_is_clear_error():
    service = AnalysisService(MockInferenceProvider())
    try:
        service.analyze([])
    except ValueError as exc:
        assert "válidas" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
