from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4


def generate_patient_id() -> str:
    return f"PT-{datetime.now():%Y%m%d}-{uuid4().hex[:6].upper()}"


@dataclass(frozen=True)
class BoundingBox:
    x: float
    y: float
    width: float
    height: float


@dataclass
class Detection:
    class_name: str
    confidence: float
    bbox: BoundingBox
    review_reasons: tuple[str, ...] = ()
    raw_class: str = ""
    model_id: str = ""
    inference_threshold: float = 0.0
    source_image: str = ""
    detection_id: str = ""
    human_review: str = "sin_revisar"
    corrected_class: str = ""
    review_note: str = ""

    @property
    def requires_review(self) -> bool:
        return bool(self.review_reasons)

    @property
    def accepted_after_review(self) -> bool:
        return self.human_review not in {"incorrecta"}

    @property
    def effective_class(self) -> str:
        return self.corrected_class or self.class_name


@dataclass(frozen=True)
class ImageQuality:
    width: int
    height: int
    brightness: float
    contrast: float
    sharpness: float
    warnings: tuple[str, ...] = ()

    @property
    def status(self) -> str:
        return "Revisar calidad" if self.warnings else "Sin alertas técnicas"


@dataclass
class ImageAnalysis:
    image_path: Path
    detections: list[Detection] = field(default_factory=list)
    inference_ms: float | None = None
    error: str | None = None
    quality: ImageQuality | None = None
    warnings: list[str] = field(default_factory=list)
    raw_detections: list[Detection] = field(default_factory=list)
    raw_response: dict | None = None
    processing_variant: str = "original"
    omitted_elements: list[dict[str, str]] = field(default_factory=list)

    def accepted_detections(self, threshold: float) -> list[Detection]:
        return [d for d in self.detections if d.confidence >= threshold]

    def hidden_detections(self, threshold: float) -> list[Detection]:
        return [d for d in self.detections if d.confidence < threshold]


@dataclass
class StudyResult:
    images: list[ImageAnalysis]
    study_id: str = field(default_factory=lambda: uuid4().hex[:10].upper())
    created_at: datetime = field(default_factory=datetime.now)
    source: str = ""
    provider_name: str = "Proveedor desconocido"
    is_simulated: bool = False
    confidence_threshold: float = 0.25
    audit_mode: bool = False
    patient_name: str = ""
    patient_id: str = field(default_factory=generate_patient_id)

    @property
    def successful_images(self) -> list[ImageAnalysis]:
        return [image for image in self.images if not image.error]

    @property
    def failed_images(self) -> list[ImageAnalysis]:
        return [image for image in self.images if image.error]

    def detections_for(self, image: ImageAnalysis) -> list[Detection]:
        return image.accepted_detections(self.confidence_threshold)

    def reviewed_detections_for(self, image: ImageAnalysis) -> list[Detection]:
        return [d for d in self.detections_for(image) if d.accepted_after_review]

    def class_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for image in self.successful_images:
            for detection in self.reviewed_detections_for(image):
                name = detection.effective_class
                counts[name] = counts.get(name, 0) + 1
        return counts

    def hidden_count(self) -> int:
        return sum(len(image.hidden_detections(self.confidence_threshold)) for image in self.successful_images)

    def review_count(self) -> int:
        return sum(d.requires_review for image in self.successful_images for d in self.detections_for(image))

    def human_review_summary(self) -> dict[str, int]:
        summary = {"sin_revisar": 0, "correcta": 0, "incorrecta": 0, "clase_equivocada": 0, "elemento_omitido": 0}
        for image in self.successful_images:
            for detection in image.detections:
                summary[detection.human_review] = summary.get(detection.human_review, 0) + 1
            summary["elemento_omitido"] += len(image.omitted_elements)
        return summary

    def average_confidence(self) -> float:
        values = [d.confidence for image in self.successful_images for d in self.detections_for(image)]
        return sum(values) / len(values) if values else 0.0

    def total_inference_ms(self) -> float:
        return sum(image.inference_ms or 0.0 for image in self.successful_images)

    def averages_per_image(self) -> dict[str, float]:
        divisor = len(self.successful_images)
        return ({name: total / divisor for name, total in self.class_counts().items()} if divisor else {})

    def fields_by_class(self) -> dict[str, int]:
        result: dict[str, int] = {}
        for image in self.successful_images:
            for name in {d.class_name for d in self.detections_for(image)}:
                result[name] = result.get(name, 0) + 1
        return result
