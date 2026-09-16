import csv
import json
from pathlib import Path

from PIL import Image
from pypdf import PdfReader
from PySide6.QtGui import QImage

from src.domain.models import BoundingBox, Detection, ImageAnalysis, StudyResult
from src.inference.mock_provider import MockInferenceProvider
from src.processing.class_normalizer import DISPLAY_NAMES, class_display_name, normalize_class_name
from src.reports.pdf_report import generate_pdf, export_annotated_images
from src.services.analysis_service import AnalysisService
from src.services.export_service import export_csv, export_json
from src.ui.image_renderer import render_analysis
from src.ui.main_window import MainWindow


def test_review_is_consistent_in_render_counts_and_exports(qtbot, tmp_path):
    image = tmp_path / 'campo & control.png'
    Image.new('RGB', (300, 200), 'white').save(image)
    rejected = Detection('eritrocitos', .99, BoundingBox(50, 100, 20, 20), human_review='incorrecta')
    corrected = Detection('leucocitos', .8, BoundingBox(180, 100, 30, 30),
                          human_review='clase_equivocada', corrected_class='cilindros')
    result = StudyResult([ImageAnalysis(image, [rejected, corrected])], patient_name='A < B & C', source='A & B')
    assert result.class_counts() == {'cilindros': 1}
    assert result.average_confidence() == .8
    export_json(result, tmp_path / 'result.json')
    data = json.loads((tmp_path / 'result.json').read_text(encoding='utf-8'))
    assert data['fields'][0]['accepted_detections'] == 1
    assert [d['status'] for d in data['detections']] == ['rejected_by_review', 'accepted']
    export_csv(result, tmp_path / 'result.csv')
    rows = list(csv.DictReader((tmp_path / 'result.csv').open(encoding='utf-8-sig')))
    assert rows[1]['display_class'] == 'Cilindros'
    rendered = render_analysis(result.images[0], {'eritrocitos'}).toImage()
    assert rendered == QImage(str(image))
    assert render_analysis(result.images[0], {'cilindros'}).toImage() != QImage(str(image))
    pdf = generate_pdf(result, tmp_path / 'report.pdf')
    text = ' '.join(page.extract_text() for page in PdfReader(pdf).pages)
    assert 'A < B & C' in text and '1 hallazgos' in text
    window = MainWindow(AnalysisService(MockInferenceProvider())); qtbot.addWidget(window)
    window._set_paths([image], 'test'); window._on_completed(result)
    assert window._detections.rowCount() == 1
    assert window._detections.item(0, 1).text() == 'Cilindros'
    assert '1 aceptadas' in window._field_details.text()
    assert window._class_filter.findData('cilindros') >= 0
    window._set_paths([image], 'new')
    assert window._count_card.text() == '—' and window._detections.rowCount() == 0


def test_csv_free_text_cannot_be_a_formula_and_same_stems_survive(tmp_path):
    a = tmp_path / 'field.png'; b = tmp_path / 'field.jpg'
    for image in (a, b): Image.new('RGB', (100, 100), 'white').save(image)
    result = StudyResult([ImageAnalysis(a, [Detection('eritrocitos', .8, BoundingBox(50, 50, 10, 10))]), ImageAnalysis(b)], patient_name='=1+1')
    export_csv(result, tmp_path / 'a.csv')
    row = next(csv.DictReader((tmp_path / 'a.csv').open(encoding='utf-8-sig')))
    assert row['patient_name'] == "'=1+1" and float(row['confidence']) == .8
    paths = export_annotated_images(result, tmp_path / 'images')
    assert len(set(paths)) == 2 and all(p.is_file() for p in paths)


def test_seven_display_labels_roundtrip():
    raw = ['eryth', 'leuko', 'epith', 'epithn', 'cast', 'cryst', 'mycete']
    expected = ['Eritrocitos', 'Leucocitos', 'Células epiteliales', 'Núcleos epiteliales', 'Cilindros', 'Cristales', 'Levaduras y hongos']
    assert [class_display_name(x) for x in raw] == expected
    for canonical, visible in DISPLAY_NAMES.items(): assert normalize_class_name(visible) == canonical


def test_repeated_analysis_releases_threads(qtbot, tmp_path):
    image = tmp_path / 'a.png'; Image.new('RGB', (640, 480), 'white').save(image)
    window = MainWindow(AnalysisService(MockInferenceProvider())); qtbot.addWidget(window)
    window._set_paths([image], 'test')
    for _ in range(3):
        window._analyze()
        qtbot.waitUntil(lambda: window._thread is None, timeout=10000)
        assert window._result and window._worker is None
    from PySide6.QtCore import QThread
    qtbot.waitUntil(lambda: not window.findChildren(QThread), timeout=2000)


def test_frozen_missing_model_never_falls_back_to_simulation(monkeypatch, tmp_path):
    import pytest
    from src import config
    monkeypatch.setattr(config.sys, 'frozen', True, raising=False)
    monkeypatch.setattr(config.sys, '_MEIPASS', str(tmp_path), raising=False)
    monkeypatch.setenv('INFERENCE_PROVIDER', 'mock')
    with pytest.raises(FileNotFoundError): config.Settings.from_environment()
