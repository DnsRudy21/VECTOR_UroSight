from pathlib import Path
from src.inference.mock_provider import MockInferenceProvider

def test_mock_provider_is_deterministic():
    provider = MockInferenceProvider()
    assert provider.predict(Path("sample.jpg")).detections == provider.predict(Path("sample.jpg")).detections
