import json
from pathlib import Path

from PIL import Image

from src.domain.models import BoundingBox, Detection, ImageAnalysis
from src.inference.base import InferenceProvider
from src.processing.class_normalizer import normalize_class_name
from src.services.audit_service import compare_thresholds
from src.services.export_service import export_audit_csv, export_audit_json, export_threshold_comparison
from src.ui.image_renderer import legend_html


class AuditProvider(InferenceProvider):
    display_name = "Audit fixture"
    def __init__(self, threshold): self.confidence_threshold = threshold
    def predict(self, path):
        return ImageAnalysis(path, [Detection("eryth", .30, BoundingBox(20,20,10,10), raw_class="eryth"),
                                    Detection("cast", .40, BoundingBox(40,40,10,10), raw_class="cast"),
                                    Detection("WBC", .60, BoundingBox(60,60,10,10), raw_class="WBC")])


def test_raw_class_survives_normalization_and_human_review(tmp_path):
    image = tmp_path/"field.png"; Image.new("RGB",(100,100),"gray").save(image)
    results, _ = compare_thresholds(AuditProvider, [image], (.25,))
    detection = results[0].images[0].detections[0]
    assert detection.raw_class in {"eryth", "cast", "WBC"}
    assert detection.class_name == normalize_class_name(detection.raw_class)
    detection.human_review = "clase_equivocada"; detection.corrected_class = "cilindros"
    assert detection.effective_class == "cilindros"
    assert results[0].human_review_summary()["clase_equivocada"] == 1


def test_dynamic_legend_contains_only_present_classes():
    legend = legend_html({"cilindros", "eritrocitos"})
    assert "cilindros" in legend and "eritrocitos" in legend
    assert "leucocitos" not in legend


def test_audit_exports_and_threshold_comparison(tmp_path):
    image = tmp_path/"field.png"; Image.new("RGB",(100,100),"gray").save(image)
    results, summaries = compare_thresholds(AuditProvider, [image])
    assert [item["total_detections"] for item in summaries] == [3, 2, 1]
    json_path = export_audit_json(results[1], tmp_path/"audit.json")
    csv_path = export_audit_csv(results[1], tmp_path/"audit.csv")
    comparison = export_threshold_comparison(summaries, tmp_path/"thresholds.json")
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert {"raw_class", "normalized_class", "human_review"} <= payload["detections"][0].keys()
    assert "raw_class" in csv_path.read_text(encoding="utf-8-sig")
    assert len(json.loads(comparison.read_text(encoding="utf-8"))["threshold_comparison"]) == 3
