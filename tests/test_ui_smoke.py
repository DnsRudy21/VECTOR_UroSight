from src.inference.mock_provider import MockInferenceProvider
from src.services.analysis_service import AnalysisService
from src.ui.main_window import MainWindow


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
