def test_default_settings_are_safe():
    from src.config import Settings, settings
    assert settings.inference_provider in {"mock", "local", "roboflow"}
    assert 0 <= settings.confidence_threshold <= 1
    assert settings.local_model_imgsz == 480
    assert Settings.from_environment().inference_provider in {"mock", "local", "roboflow"}


def test_default_local_model_path_matches_packaged_model(monkeypatch):
    from src.config import Settings
    monkeypatch.delenv("LOCAL_MODEL_PATH", raising=False)
    assert Settings.from_environment().local_model_path.as_posix() == "models/vector_urosight/best.pt"


def test_model_image_size_must_be_positive_multiple_of_32(monkeypatch):
    from src.config import Settings
    monkeypatch.setenv("LOCAL_MODEL_IMGSZ", "481")
    with __import__("pytest").raises(ValueError, match="múltiplo de 32"):
        Settings.from_environment()
