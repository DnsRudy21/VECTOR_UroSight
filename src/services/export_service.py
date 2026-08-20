import csv
import json
from pathlib import Path

from src.domain.models import StudyResult


def detection_rows(result: StudyResult) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for image in result.images:
        if image.error:
            rows.append({"study_id": result.study_id, "provider": result.provider_name,
                         "patient_id": result.patient_id, "patient_name": result.patient_name,
                         "image": image.image_path.name, "status": "error", "error": image.error})
        for detection in image.detections:
            rows.append({"study_id": result.study_id, "provider": result.provider_name,
                         "patient_id": result.patient_id, "patient_name": result.patient_name,
                         "simulated": result.is_simulated, "threshold": result.confidence_threshold,
                         "image": image.image_path.name, "source_image": detection.source_image or image.image_path.name,
                         "processing_variant": image.processing_variant, "detection_id": detection.detection_id,
                         "raw_class": detection.raw_class or detection.class_name,
                         "normalized_class": detection.class_name, "effective_class": detection.effective_class,
                         "model": detection.model_id, "confidence": round(detection.confidence, 4),
                         "status": "accepted" if detection.confidence >= result.confidence_threshold else "discarded_by_threshold",
                         "requires_review": detection.requires_review,
                         "review_reasons": "; ".join(detection.review_reasons),
                         "human_review": detection.human_review, "corrected_class": detection.corrected_class,
                         "review_note": detection.review_note,
                         "x": round(detection.bbox.x, 2), "y": round(detection.bbox.y, 2),
                         "width": round(detection.bbox.width, 2), "height": round(detection.bbox.height, 2), "error": ""})
    return rows


def export_json(result: StudyResult, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = []
    for image in result.images:
        accepted = image.accepted_detections(result.confidence_threshold)
        fields.append({"image": image.image_path.name, "processing_variant": image.processing_variant,
                       "status": "error" if image.error else "processed", "error": image.error,
                       "total_raw_detections": len(image.raw_detections), "accepted_detections": len(accepted),
                       "discarded_by_threshold": len(image.hidden_detections(result.confidence_threshold)),
                       "average_confidence": sum(d.confidence for d in accepted)/len(accepted) if accepted else 0,
                       "inference_ms": image.inference_ms, "omitted_elements": image.omitted_elements,
                       "quality": None if not image.quality else {"resolution": [image.quality.width, image.quality.height],
                           "brightness": image.quality.brightness, "contrast": image.quality.contrast,
                           "sharpness_edge_variance": image.quality.sharpness, "warnings": list(image.quality.warnings)},
                       "warnings": image.warnings})
    payload = {"study_id": result.study_id, "created_at": result.created_at.isoformat(), "source": result.source,
               "patient": {"id": result.patient_id, "name": result.patient_name},
               "provider": {"name": result.provider_name, "simulated": result.is_simulated},
               "confidence_threshold": result.confidence_threshold, "audit_mode": result.audit_mode,
               "summary": {"processed_images": len(result.successful_images), "failed_images": len(result.failed_images),
                           "class_counts_after_review": result.class_counts(), "average_per_image": result.averages_per_image(),
                           "average_confidence": result.average_confidence(), "discarded_by_threshold": result.hidden_count(),
                           "requires_review": result.review_count()}, "review_summary": result.human_review_summary(),
               "fields": fields,
               "diagnostic_raw_responses": {image.image_path.name: image.raw_response for image in result.images if image.raw_response is not None},
               "detections": detection_rows(result)}
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def export_csv(result: StudyResult, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["study_id", "patient_id", "patient_name", "provider", "simulated", "threshold", "image", "source_image", "processing_variant",
              "detection_id", "raw_class", "normalized_class", "effective_class", "model", "confidence", "status",
              "requires_review", "review_reasons", "human_review", "corrected_class", "review_note",
              "x", "y", "width", "height", "error"]
    with output_path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(detection_rows(result))
    return output_path


export_audit_json = export_json
export_audit_csv = export_csv


def export_threshold_comparison(summaries: list[dict[str, object]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({"threshold_comparison": summaries}, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path
