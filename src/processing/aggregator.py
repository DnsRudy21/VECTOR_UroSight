import math

from src.domain.models import BoundingBox, Detection, ImageAnalysis, StudyResult
from src.processing.class_normalizer import normalize_class_name

KNOWN_CLASSES = {"eritrocitos", "leucocitos", "celulas_epiteliales", "celulas_epiteliales_nucleadas",
                 "cristales", "cilindros", "levaduras_hongos"}


def intersection_over_union(first: BoundingBox, second: BoundingBox) -> float:
    ax1, ay1, ax2, ay2 = first.x-first.width/2, first.y-first.height/2, first.x+first.width/2, first.y+first.height/2
    bx1, by1, bx2, by2 = second.x-second.width/2, second.y-second.height/2, second.x+second.width/2, second.y+second.height/2
    overlap = max(0.0, min(ax2, bx2)-max(ax1, bx1)) * max(0.0, min(ay2, by2)-max(ay1, by1))
    union = first.width*first.height + second.width*second.height - overlap
    return overlap / union if union > 0 else 0.0


def _sanitize(detection: Detection, width: int, height: int) -> Detection | None:
    values = (detection.confidence, detection.bbox.x, detection.bbox.y, detection.bbox.width, detection.bbox.height)
    if not all(math.isfinite(value) for value in values) or not 0 <= detection.confidence <= 1:
        return None
    box = detection.bbox
    x1, y1 = max(0.0, box.x-box.width/2), max(0.0, box.y-box.height/2)
    x2, y2 = min(float(width), box.x+box.width/2), min(float(height), box.y+box.height/2)
    if x2 <= x1 or y2 <= y1:
        return None
    reasons = list(detection.review_reasons)
    if (x1, y1, x2, y2) != (box.x-box.width/2, box.y-box.height/2, box.x+box.width/2, box.y+box.height/2):
        reasons.append("Caja ajustada a los límites de la imagen")
    name = normalize_class_name(detection.class_name)
    if name not in KNOWN_CLASSES:
        reasons.append("Clase no reconocida")
    return Detection(name, detection.confidence, BoundingBox((x1+x2)/2, (y1+y2)/2, x2-x1, y2-y1),
                     tuple(reasons), detection.raw_class or detection.class_name, detection.model_id,
                     detection.inference_threshold, detection.source_image, detection.detection_id,
                     detection.human_review, detection.corrected_class, detection.review_note)


def _nms(detections: list[Detection], threshold: float = 0.5) -> list[Detection]:
    kept: list[Detection] = []
    for candidate in sorted(detections, key=lambda item: item.confidence, reverse=True):
        if any(candidate.class_name == other.class_name and intersection_over_union(candidate.bbox, other.bbox) >= threshold for other in kept):
            continue
        kept.append(candidate)
    return kept


def normalize_study(result: StudyResult) -> StudyResult:
    images: list[ImageAnalysis] = []
    for image in result.images:
        width = image.quality.width if image.quality else 1_000_000
        height = image.quality.height if image.quality else 1_000_000
        sanitized = [item for detection in image.detections if (item := _sanitize(detection, width, height))]
        duplicates = len(sanitized) - len(_nms(sanitized))
        warnings = list(image.warnings)
        if duplicates:
            warnings.append(f"{duplicates} caja(s) duplicada(s) suprimida(s) por IoU")
        images.append(ImageAnalysis(image.image_path, _nms(sanitized), image.inference_ms, image.error,
                                    image.quality, warnings, list(image.detections), image.raw_response,
                                    image.processing_variant, list(image.omitted_elements)))
    return StudyResult(images, result.study_id, result.created_at, result.source, result.provider_name,
                       result.is_simulated, result.confidence_threshold, result.audit_mode,
                       result.patient_name, result.patient_id)
