import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from src.config import settings
from src.inference.local_yolo_provider import LocalYoloProvider
from src.inference.mock_provider import MockInferenceProvider
from src.inference.roboflow_provider import RoboflowProvider
from src.services.analysis_service import AnalysisService
from src.ui.main_window import MainWindow

def build_provider():
    if settings.inference_provider == "roboflow":
        return RoboflowProvider(settings.roboflow_api_key, settings.roboflow_model_id,
                                settings.confidence_threshold,
                                diagnostic=settings.roboflow_diagnostic)
    if settings.inference_provider == "local":
        return LocalYoloProvider(settings.local_model_path, settings.confidence_threshold)
    return MockInferenceProvider()

def main() -> int:
    app = QApplication(sys.argv)
    try:
        provider = build_provider()
    except Exception as exc:
        QMessageBox.critical(None, "No se pudo iniciar VECTOR UroSight", str(exc))
        return 2
    window = MainWindow(AnalysisService(provider))
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
