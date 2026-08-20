from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from src.domain.models import StudyResult
from src.services.analysis_service import AnalysisService


class AnalysisWorker(QObject):
    progress = Signal(int, int, str)
    completed = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, service: AnalysisService, paths: list[Path], source: str) -> None:
        super().__init__()
        self._service = service
        self._paths = paths
        self._source = source
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    @Slot()
    def run(self) -> None:
        try:
            result: StudyResult = self._service.analyze(
                self._paths,
                lambda done, total, path: self.progress.emit(done, total, path.name),
                lambda: self._cancelled,
                self._source,
            )
            self.completed.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()
