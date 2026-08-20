from collections.abc import Callable
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from src.domain.models import ImageAnalysis, StudyResult
from src.inference.base import InferenceProvider
from src.processing.aggregator import normalize_study
from src.processing.image_quality import assess_image_quality


class AnalysisService:
    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

    def __init__(self, provider: InferenceProvider) -> None:
        self._provider = provider

    @property
    def provider_name(self) -> str:
        return self._provider.display_name

    @property
    def is_simulated(self) -> bool:
        return self._provider.is_simulated

    @property
    def confidence_threshold(self) -> float:
        return self._provider.confidence_threshold

    @classmethod
    def validate_image(cls, path: Path) -> tuple[bool, str]:
        if not path.is_file():
            return False, "El archivo no existe."
        if path.suffix.lower() not in cls.SUPPORTED_EXTENSIONS:
            return False, "Formato no compatible."
        try:
            with Image.open(path) as image:
                image.verify()
        except (OSError, UnidentifiedImageError):
            return False, "El archivo no contiene una imagen válida."
        return True, ""

    @classmethod
    def collect_folder(cls, folder: Path) -> list[Path]:
        if not folder.is_dir():
            return []
        return sorted((p for p in folder.iterdir() if p.is_file() and
                       p.suffix.lower() in cls.SUPPORTED_EXTENSIONS), key=lambda p: p.name.lower())

    def analyze(
        self,
        image_paths: list[Path],
        progress: Callable[[int, int, Path], None] | None = None,
        should_cancel: Callable[[], bool] | None = None,
        source: str = "",
    ) -> StudyResult:
        valid = [path for path in image_paths if self.validate_image(path)[0]]
        if not valid:
            raise ValueError("No se seleccionaron imágenes válidas y compatibles.")
        images: list[ImageAnalysis] = []
        for index, path in enumerate(valid, start=1):
            if should_cancel and should_cancel():
                break
            try:
                quality = assess_image_quality(path)
                analysis = self._provider.predict(path)
                analysis.quality = quality
                images.append(analysis)
            except Exception as exc:
                images.append(ImageAnalysis(image_path=path, error=str(exc)))
            if progress:
                progress(index, len(valid), path)
        if not images:
            raise RuntimeError("El análisis fue cancelado antes de procesar imágenes.")
        return normalize_study(StudyResult(images=images, source=source,
                                           provider_name=self.provider_name,
                                           is_simulated=self.is_simulated,
                                           confidence_threshold=self.confidence_threshold))
