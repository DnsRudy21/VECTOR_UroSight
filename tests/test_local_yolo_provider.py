from types import SimpleNamespace
import sys

import numpy as np
import pytest

from src.inference.local_yolo_provider import LocalYoloProvider


def test_saturation_is_visible_and_class_ids_come_from_checkpoint(tmp_path, monkeypatch):
    model = tmp_path / 'best.pt'; model.touch()
    calls = []
    box = SimpleNamespace(cls=np.array(4), conf=np.array(.8), xyxy=np.array([[0., 0., 10., 20.]]))
    result = SimpleNamespace(boxes=[box], names={4: 'cast'}, speed={'inference': 2.})
    def predict(**kwargs):
        calls.append(kwargs)
        return [result]
    monkeypatch.setitem(sys.modules, 'ultralytics', SimpleNamespace(YOLO=lambda _: SimpleNamespace(predict=predict)))
    provider = LocalYoloProvider(model, max_detections=1)
    analysis = provider.predict(tmp_path / 'image.png')
    assert calls[0]['max_det'] == 1 and 'classes' not in calls[0]
    assert analysis.detections[0].raw_class == 'cast'
    assert analysis.detections[0].bbox.width == 10.
    assert any('truncamiento' in warning for warning in analysis.warnings)


@pytest.mark.parametrize('value', [0, -1, 1.5, True])
def test_invalid_detection_limit_is_rejected_before_loading(tmp_path, value):
    with pytest.raises(ValueError):
        LocalYoloProvider(tmp_path / 'unused.pt', max_detections=value)
