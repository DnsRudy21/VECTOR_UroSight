import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

from src.inference.local_yolo_provider import LocalYoloProvider
from src.inference.roboflow_provider import RoboflowProvider


class Response:
    def __init__(self, payload=None, status_code=200, json_error=None):
        self.payload, self.status_code, self.json_error = payload, status_code, json_error

    def json(self):
        if self.json_error: raise self.json_error
        return self.payload


class Session:
    def __init__(self, response=None, error=None):
        self.response, self.error, self.calls = response, error, []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if self.error: raise self.error
        return self.response


def image_file(tmp_path: Path) -> Path:
    path = tmp_path / "field with spaces.png"; path.write_bytes(b"controlled-image-bytes"); return path


def test_roboflow_rest_contract_without_network(tmp_path):
    session = Session(Response({"predictions": [{"class": "RBC", "confidence": .88,
        "x": 40, "y": 50, "width": 20, "height": 30}]}))
    result = RoboflowProvider("secret-test-key", "urine-model/7", .42, session=session).predict(image_file(tmp_path))
    url, request = session.calls[0]
    assert url == "https://detect.roboflow.com/urine-model/7"
    assert request["params"]["confidence"] == 42
    assert request["params"]["api_key"] == "secret-test-key"
    assert request["timeout"] == (10.0, 60.0)
    assert request["headers"]["Content-Type"] == "application/x-www-form-urlencoded"
    assert result.detections[0].confidence == .88
    assert result.detections[0].bbox.width == 20
    assert RoboflowProvider("key", "model/1", .42, session=session).confidence_threshold == .42
    assert result.detections[0].raw_class == "RBC"
    assert result.detections[0].model_id == "urine-model/7"
    assert result.raw_response is None


def test_roboflow_keeps_raw_json_only_in_diagnostic_mode(tmp_path):
    payload = {"predictions": []}
    result = RoboflowProvider("secret", "model/1", session=Session(Response(payload)), diagnostic=True).predict(image_file(tmp_path))
    assert result.raw_response == payload


@pytest.mark.parametrize(("status", "error_type"), [(401, PermissionError), (403, PermissionError),
    (404, LookupError), (408, TimeoutError), (429, RuntimeError), (500, RuntimeError)])
def test_roboflow_maps_http_errors_without_exposing_key(tmp_path, status, error_type):
    provider = RoboflowProvider("never-expose-this-key", "model/1", session=Session(Response({}, status)))
    with pytest.raises(error_type) as captured: provider.predict(image_file(tmp_path))
    assert "never-expose-this-key" not in str(captured.value)


@pytest.mark.parametrize(("error", "error_type"), [(requests.Timeout(), TimeoutError),
    (requests.ConnectionError(), ConnectionError)])
def test_roboflow_maps_transport_errors(tmp_path, error, error_type):
    provider = RoboflowProvider("secret", "model/1", session=Session(error=error))
    with pytest.raises(error_type): provider.predict(image_file(tmp_path))


def test_roboflow_rejects_unexpected_json(tmp_path):
    provider = RoboflowProvider("secret", "model/1", session=Session(Response({"predictions": "invalid"})))
    with pytest.raises(ValueError, match="lista de predicciones"):
        provider.predict(image_file(tmp_path))


def test_local_yolo_contract_without_heavy_model(monkeypatch, tmp_path):
    class Scalar:
        def __init__(self, value): self.value = value
        def item(self): return self.value
    class Coordinates:
        def __getitem__(self, _index): return self
        def tolist(self): return [10, 20, 50, 70]
    box = SimpleNamespace(cls=Scalar(0), conf=Scalar(.91), xyxy=Coordinates())
    result = SimpleNamespace(boxes=[box], names={0: "WBC"}, speed={"inference": 7.5})
    class YOLO:
        def __init__(self, _path): pass
        def predict(self, **_kwargs): return [result]
    monkeypatch.setitem(sys.modules, "ultralytics", SimpleNamespace(YOLO=YOLO))
    weights = tmp_path / "controlled.pt"; weights.write_bytes(b"fixture")
    analysis = LocalYoloProvider(weights).predict(Path("field.png"))
    assert analysis.detections[0].bbox.width == 40
    assert analysis.detections[0].confidence == .91
    assert analysis.inference_ms == 7.5
    assert analysis.detections[0].raw_class == "WBC"
    assert analysis.detections[0].model_id == "controlled.pt"
    assert analysis.detections[0].inference_threshold == .25
    assert analysis.detections[0].source_image == "field.png"
