from abc import ABC, abstractmethod
from pathlib import Path

from src.domain.models import ImageAnalysis


class InferenceProvider(ABC):
    display_name = "Proveedor desconocido"
    is_simulated = False
    confidence_threshold = 0.25

    @abstractmethod
    def predict(self, image_path: Path) -> ImageAnalysis:
        raise NotImplementedError
