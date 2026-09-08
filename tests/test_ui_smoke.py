from src.inference.mock_provider import MockInferenceProvider
from src.services.analysis_service import AnalysisService
from src.ui.main_window import MainWindow
from src.domain.models import BoundingBox, Detection, ImageAnalysis, StudyResult
from src.processing.aggregator import KNOWN_CLASSES
from pathlib import Path


def test_main_window_starts(qtbot):
    window = MainWindow(AnalysisService(MockInferenceProvider()))
    qtbot.addWidget(window)
    assert "VECTOR UroSight" in window.windowTitle()
    assert "RESULTADOS SIMULADOS" in window._provider_badge.text()
    assert window._analyze_button.text() == "Analizar estudio"
    assert not window._analyze_button.isEnabled()
    assert window._theme == "light"
    window._toggle_theme()
    assert window._theme == "dark"
    assert window._theme_switch._dark
    assert window._export_button.text() == "Exportar ▾"
    assert [action.text() for action in window._export_button.menu().actions()] == [
        "Reporte clínico PDF", "Imágenes anotadas", "Estadísticas CSV"
    ]
    assert window.minimumWidth() >= 1120


def test_nucleus_filter_and_review_store_canonical_ids(qtbot):
    window = MainWindow(AnalysisService(MockInferenceProvider()))
    qtbot.addWidget(window)
    canonical = 'celulas_epiteliales_nucleadas'
    window._result = StudyResult([ImageAnalysis(Path('unused.png'),
        [Detection(canonical, .8, BoundingBox(10, 10, 5, 5), raw_class='epithn')])])
    window._update_study_results()
    index = window._class_filter.findText('Núcleos epiteliales')
    assert index >= 0 and window._class_filter.itemData(index) == canonical
    assert {window._corrected_class.itemData(i) for i in range(window._corrected_class.count())} == KNOWN_CLASSES
    window._corrected_class.setCurrentText('Núcleos epiteliales')
    assert window._review_class_value() == canonical
    window._corrected_class.setEditText('cast')
    assert window._review_class_value() == 'cilindros'
