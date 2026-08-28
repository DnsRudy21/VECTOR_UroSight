import json
import sys
from pathlib import Path
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
        return LocalYoloProvider(settings.local_model_path, settings.confidence_threshold,
                                 settings.local_model_imgsz)
    return MockInferenceProvider()


def run_portable_smoke_test(images_directory: Path, output: Path) -> int:
    """Exercise the frozen provider without opening the GUI."""
    service = AnalysisService(build_provider())
    images = service.collect_folder(images_directory)
    result = service.analyze(images, source="portable-smoke-test")
    payload = {
        "provider": result.provider_name,
        "images": len(result.images),
        "successful_images": len(result.successful_images),
        "failed_images": len(result.failed_images),
        "detections": sum(len(result.detections_for(image)) for image in result.successful_images),
        "errors": [
            {"image": image.image_path.name, "error": image.error}
            for image in result.failed_images
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0 if not result.failed_images and result.successful_images else 3

def main() -> int:
    if len(sys.argv) == 4 and sys.argv[1] == "--portable-smoke-test":
        return run_portable_smoke_test(Path(sys.argv[2]), Path(sys.argv[3]))
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
