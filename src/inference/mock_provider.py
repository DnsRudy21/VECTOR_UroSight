from pathlib import Path
import random
import time
from src.domain.models import BoundingBox, Detection, ImageAnalysis
from src.inference.base import InferenceProvider

class MockInferenceProvider(InferenceProvider):
    display_name = "Demostración simulada"
    is_simulated = True
    CLASSES = ("rbc", "wbc", "epithelial")

    def predict(self, image_path: Path) -> ImageAnalysis:
        start = time.perf_counter()
        rng = random.Random(sum(image_path.name.encode("utf-8")))
        detections = []
        for _ in range(rng.randint(3, 12)):
            detections.append(
                Detection(
                    class_name=rng.choice(self.CLASSES),
                    confidence=round(rng.uniform(0.55, 0.98), 3),
                    bbox=BoundingBox(
                        x=rng.uniform(100, 500),
                        y=rng.uniform(100, 400),
                        width=rng.uniform(25, 90),
                        height=rng.uniform(25, 90),
                    ),
                )
            )
        return ImageAnalysis(
            image_path=image_path,
            detections=detections,
            inference_ms=(time.perf_counter() - start) * 1000,
        )
