from collections.abc import Callable
from pathlib import Path

from src.domain.models import StudyResult
from src.inference.base import InferenceProvider
from src.services.analysis_service import AnalysisService


def summarize_threshold(result: StudyResult, threshold: float) -> dict[str, object]:
    result.confidence_threshold = threshold
    per_image = []
    for image in result.successful_images:
        detections = result.detections_for(image)
        per_image.append({"image": image.image_path.name, "total": len(detections),
                          "classes": sorted({d.class_name for d in detections}),
                          "average_confidence": sum(d.confidence for d in detections)/len(detections) if detections else 0})
    detections = [d for image in result.successful_images for d in result.detections_for(image)]
    return {"threshold": threshold, "total_detections": len(detections),
            "classes": sorted({d.class_name for d in detections}),
            "average_confidence": sum(d.confidence for d in detections)/len(detections) if detections else 0,
            "per_image": per_image}


def compare_thresholds(provider_factory: Callable[[float], InferenceProvider], image_paths: list[Path],
                       thresholds: tuple[float, ...] = (.25, .35, .50)) -> tuple[list[StudyResult], list[dict[str, object]]]:
    results, summaries = [], []
    for threshold in thresholds:
        result = AnalysisService(provider_factory(threshold)).analyze(image_paths, source=f"Auditoría {threshold:.2f}")
        result.audit_mode = True; result.confidence_threshold = threshold
        results.append(result); summaries.append(summarize_threshold(result, threshold))
    return results, summaries
