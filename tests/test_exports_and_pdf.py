import json

from PIL import Image
from pypdf import PdfReader

from src.inference.mock_provider import MockInferenceProvider
from src.reports.pdf_report import export_annotated_images, generate_pdf
from src.services.analysis_service import AnalysisService
from src.services.export_service import export_csv, export_json


def test_structured_exports_and_readable_pdf(tmp_path):
    image_path = tmp_path / "campo.png"
    Image.new("RGB", (640, 480), "white").save(image_path)
    result = AnalysisService(MockInferenceProvider()).analyze([image_path], source="Prueba")
    result.patient_name = "Paciente de prueba"
    result.patient_id = "PT-20260819-ABC123"
    json_path = export_json(result, tmp_path / "result.json")
    csv_path = export_csv(result, tmp_path / "result.csv")
    pdf_path = generate_pdf(result, tmp_path / "report.pdf")
    annotated = export_annotated_images(result, tmp_path / "annotated")
    assert json.loads(json_path.read_text(encoding="utf-8"))["study_id"] == result.study_id
    assert json.loads(json_path.read_text(encoding="utf-8"))["patient"] == {
        "id": "PT-20260819-ABC123", "name": "Paciente de prueba"
    }
    assert json.loads(json_path.read_text(encoding="utf-8"))["provider"]["simulated"] is True
    assert "study_id" in csv_path.read_text(encoding="utf-8-sig")
    reader = PdfReader(str(pdf_path))
    text = " ".join(page.extract_text() or "" for page in reader.pages)
    assert "VECTOR UroSight" in text
    assert result.study_id in text
    assert "PT-20260819-ABC123" in text
    assert "Paciente de prueba" in text
    assert "Demostración simulada" in text
    assert "RESULTADOS SIMULADOS" in text
    assert len(reader.pages) >= 2
    assert len(annotated) == 1
    assert annotated[0].is_file()
    with Image.open(annotated[0]) as exported:
        assert exported.size == (640, 480)


def test_pdf_includes_every_field_in_compact_adaptive_gallery(tmp_path):
    image_paths = []
    for index in range(13):
        image_path = tmp_path / f"campo_{index + 1:02d}.png"
        Image.new("RGB", (320, 240), "white").save(image_path)
        image_paths.append(image_path)
    result = AnalysisService(MockInferenceProvider()).analyze(image_paths, source="Prueba de galería")
    pdf_path = generate_pdf(result, tmp_path / "gallery.pdf")
    reader = PdfReader(str(pdf_path))
    text = " ".join(page.extract_text() or "" for page in reader.pages)
    assert all(path.name in text for path in image_paths)
    assert "13 de 13 campos incluidos" in text
    assert len(reader.pages) <= 4
