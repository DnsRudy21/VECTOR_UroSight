from pathlib import Path
from src.domain.models import BoundingBox, Detection, ImageAnalysis
from src.inference.base import InferenceProvider

class LocalYoloProvider(InferenceProvider):
    display_name = "YOLO local"
    is_simulated = False
    def __init__(self, model_path: Path, confidence: float = 0.25) -> None:
        if not model_path.exists():
            raise FileNotFoundError(f"No existe el modelo local: {model_path}")
        from ultralytics import YOLO
        self._model = YOLO(str(model_path))
        self.model_path = model_path
        self.model_id = model_path.name
        self._confidence = confidence
        self.confidence_threshold = confidence

    def predict(self, image_path: Path) -> ImageAnalysis:
        result = self._model.predict(
            source=str(image_path),
            conf=self._confidence,
            verbose=False,
        )[0]
        detections = []
        for box in result.boxes:
            cls_id = int(box.cls.item())
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            raw_class = str(result.names[cls_id])
            detections.append(
                Detection(
                    class_name=raw_class,
                    confidence=float(box.conf.item()),
                    bbox=BoundingBox(
                        x=(x1 + x2) / 2,
                        y=(y1 + y2) / 2,
                        width=x2 - x1,
                        height=y2 - y1,
                    ),
                    raw_class=raw_class,
                    model_id=self.model_id,
                    inference_threshold=self._confidence,
                    source_image=str(image_path),
                )
            )
        speed = getattr(result, "speed", {}) or {}
        return ImageAnalysis(
            image_path=image_path,
            detections=detections,
            inference_ms=float(speed.get("inference", 0.0)),
        )
