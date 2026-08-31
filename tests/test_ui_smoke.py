from src.inference.mock_provider import MockInferenceProvider
from src.services.analysis_service import AnalysisService
from src.ui.main_window import MainWindow


def test_main_window_starts(qtbot):
    window = MainWindow(AnalysisService(MockInferenceProvider()))
    qtbot.addWidget(window)
    assert "VECTOR UroSight" in window.windowTitle()
    assert "RESULTADOS SIMULADOS" in window._provider_badge.text()
    assert window._analyze_button.text() == "Analizar estudio →"
    assert window._export_button.text() == "Exportar reporte"
    assert window.minimumWidth() >= 1120
