from pathlib import Path

from PIL import Image
import pytest
from PySide6.QtCore import QMimeData, QPoint, QPointF, Qt, QUrl, QTimer
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QPushButton

from src.domain.models import StudyResult
from src.inference.mock_provider import MockInferenceProvider
from src.services.analysis_service import AnalysisService
from src.ui.main_window import MainWindow


def window(qtbot):
    w = MainWindow(AnalysisService(MockInferenceProvider()))
    qtbot.addWidget(w)
    w.show()
    return w


def picture(path):
    Image.new('RGB', (32, 32), 'white').save(path)
    return path


def test_direct_file_and_folder_buttons(qtbot, monkeypatch, tmp_path):
    w = window(qtbot)
    a = picture(tmp_path / 'a.png')
    b = picture(tmp_path / 'b.jpg')
    monkeypatch.setattr(QFileDialog, 'getOpenFileNames', lambda *args: ([str(a)], ''))
    qtbot.mouseClick(w._add_files_button, Qt.LeftButton)
    assert w._selected_paths == [a]
    monkeypatch.setattr(QFileDialog, 'getExistingDirectory', lambda *args: str(tmp_path))
    qtbot.mouseClick(w._add_folder_button, Qt.LeftButton)
    assert w._selected_paths == [a, b]


@pytest.mark.parametrize('surface', ['_files', '_viewer'])
def test_mixed_drop_on_child_view_deduplicates_and_rejects_remote(qtbot, tmp_path, surface):
    w = window(qtbot)
    a = picture(tmp_path / 'a.png')
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(a)), QUrl.fromLocalFile(str(tmp_path)), QUrl('https://example.invalid/photo.png')])
    target = getattr(w, surface).viewport()
    enter = QDragEnterEvent(QPoint(10, 10), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
    QApplication.sendEvent(target, enter)
    assert enter.isAccepted()
    drop = QDropEvent(QPointF(10, 10), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
    QApplication.sendEvent(target, drop)
    assert drop.isAccepted() and w._selected_paths == [a]
    remote = QMimeData()
    remote.setUrls([QUrl('https://example.invalid/photo.png')])
    assert not w._can_drop(remote)


def test_loading_is_blocked_during_analysis(qtbot, monkeypatch, tmp_path):
    w = window(qtbot)
    a = picture(tmp_path / 'a.png')
    monkeypatch.setattr(w, '_is_analyzing', lambda: True)
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(a))])
    assert not w._can_drop(mime)
    w._set_paths([a], 'test')
    assert w._selected_paths == []


def test_export_dialog_dispatches_selected_action(qtbot, monkeypatch):
    w = window(qtbot)
    w._result = StudyResult([])
    calls = []
    monkeypatch.setattr(w, '_export_csv', lambda: calls.append('csv'))

    def choose():
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, QDialog)
        buttons = {b.text(): b for b in dialog.findChildren(QPushButton)}
        assert set(buttons) == {'Guardar reporte PDF', 'Guardar imágenes anotadas', 'Guardar estadísticas CSV', 'Cancelar'}
        buttons['Guardar estadísticas CSV'].click()

    QTimer.singleShot(0, choose)
    w._show_export_options()
    assert calls == ['csv']
