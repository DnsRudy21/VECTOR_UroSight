"""Opt-in end-to-end acceptance harness for the actual source or frozen GUI.

Uses real Qt events, model inference, review handlers and export writers. File
dialog choices are supplied by the harness; it never substitutes model results.
"""
import json
import os
import socket
from pathlib import Path
import sys
import time
import traceback

from PySide6.QtCore import QMimeData, QPoint, QPointF, Qt, QTimer, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont, QFontDatabase
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from src.services.analysis_service import AnalysisService
from src.ui.main_window import MainWindow


def run(images_dir: Path, output: Path, provider_factory) -> int:
    started = time.perf_counter()
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")
    for name in ('segoeui.ttf', 'segoeuib.ttf', 'seguisb.ttf', 'seguisym.ttf'):
        font = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts' / name
        if font.exists(): QFontDatabase.addApplicationFont(str(font))
    app.setFont(QFont('Segoe UI', 9))
    report = {'frozen': bool(getattr(sys, 'frozen', False)), 'executable': sys.executable,
              'cwd': str(Path.cwd()), 'checks': [], 'messages': [], 'success': False,
              'scope': 'Real Qt/model/exports; file-dialog choices automated; no simulated detections'}
    network_connect = socket.socket.connect
    def deny_network(*args, **kwargs):
        raise OSError('Network disabled during offline acceptance test')
    socket.socket.connect = deny_network
    report['offline_guard'] = 'Python socket connections disabled during the complete test'
    originals = {key: getattr(QFileDialog, key) for key in ('getOpenFileNames', 'getExistingDirectory', 'getSaveFileName')}
    notices = {key: getattr(QMessageBox, key) for key in ('critical', 'warning', 'information')}
    windows = []
    timer = QTimer(); timer.setInterval(25)
    state = {'phase': 0, 'ticks': 0}

    def check(condition, label):
        if not condition: raise AssertionError(label)
        report['checks'].append(label)

    def finish(error=None):
        timer.stop()
        if error: report['error'] = error
        report['success'] = error is None
        report['wall_seconds'] = time.perf_counter() - started
        (output / 'smoke.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        for name, value in originals.items(): setattr(QFileDialog, name, value)
        for name, value in notices.items(): setattr(QMessageBox, name, value)
        socket.socket.connect = network_connect
        for window in windows: window.close()
        app.exit(0 if error is None else 3)

    def tick():
        try:
            if time.perf_counter() - started > 240: raise TimeoutError('GUI smoke exceeded 240 seconds')
            state['ticks'] += 1
            w = windows[-1]
            phase = state['phase']
            if phase == 0:
                report['window_visible_seconds'] = time.perf_counter() - started
                w.grab().save(str(output / '01_inicio.png'))
                check(w.isVisible() and not w._service.is_simulated, 'window opens with real provider')
                images = w._service.collect_folder(images_dir)
                check(len(images) >= 2, 'at least two demo images')
                state['images'] = images
                QFileDialog.getOpenFileNames = lambda *a: ([str(images[0])], '')
                w._add_files_button.click(); check(w._selected_paths == images[:1], 'single file button')
                QFileDialog.getOpenFileNames = lambda *a: ([str(p) for p in images[:2]], '')
                w._add_files_button.click(); check(len(w._selected_paths) == 2, 'multiple file button')
                empty = output / 'empty'; empty.mkdir(exist_ok=True)
                QFileDialog.getExistingDirectory = lambda *a: str(empty)
                w._add_folder_button.click(); check('Carpeta vacía' in str(report['messages']), 'empty folder handled')
                bad = output / 'invalid.png'; bad.write_text('not an image')
                w._set_paths([bad], 'invalid'); check(not w._selected_paths, 'invalid image rejected')
                QFileDialog.getExistingDirectory = lambda *a: str(images_dir)
                w._add_folder_button.click(); check(len(w._selected_paths) == len(images), 'folder button')
                mime = QMimeData(); mime.setUrls([QUrl.fromLocalFile(str(images_dir)), QUrl.fromLocalFile(str(images[0]))])
                target = w._viewer.viewport()
                enter = QDragEnterEvent(QPoint(10, 10), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
                QApplication.sendEvent(target, enter)
                drop = QDropEvent(QPointF(10, 10), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
                QApplication.sendEvent(target, drop)
                check(drop.isAccepted() and len(w._selected_paths) == len(images), 'folder and file drag drop deduplicated')
                state['analysis_start'] = time.perf_counter(); state['initial_ticks'] = state['ticks']
                w._analyze_button.click(); state['phase'] = 1
            elif phase == 1:
                if w._thread is not None: return
                result = w._result
                check(result is not None and not result.failed_images, 'background real inference completes')
                check(state['ticks'] - state['initial_ticks'] > 1, 'Qt heartbeat responds during inference')
                report['batch_wall_seconds'] = time.perf_counter() - state['analysis_start']
                report['images'] = len(result.images); report['inference_ms'] = result.total_inference_ms()
                report['counts_before_review'] = result.class_counts()
                check(w._progress.value() == len(result.images), 'progress completes')
                check(w._files.count() == len(result.images), 'thumbnails retained')
                w._view_mode.setCurrentIndex(1); check(not w._viewer._item.pixmap().isNull(), 'original image visible')
                w._view_mode.setCurrentIndex(0)
                w.grab().save(str(output / '02_resultados.png'))
                index = next(i for i, image in enumerate(result.images) if len(result.reviewed_detections_for(image)) >= 2)
                w._files.setCurrentRow(index); w._audit_mode.setChecked(True)
                w._detection_selected(0, 0); w._review_status.setCurrentText('incorrecta'); w._apply_review()
                check(result.images[index].detections[0].human_review == 'incorrecta', 'human rejection saved')
                w._detection_selected(1, 0); w._review_status.setCurrentText('clase_equivocada')
                correction = 'cilindros' if result.images[index].detections[1].class_name != 'cilindros' else 'eritrocitos'
                w._corrected_class.setCurrentIndex(w._corrected_class.findData(correction)); w._apply_review()
                check(result.images[index].detections[1].effective_class == correction, 'human reclassification saved')
                w._class_filter.setCurrentIndex(w._class_filter.findData(correction))
                check(w._detections.rowCount() > 0, 'corrected class filter works')
                w._class_filter.setCurrentIndex(0); w._audit_mode.setChecked(False)
                w.grab().save(str(output / '03_revision.png'))
                for suffix, action in (('json', w._export_json), ('csv', w._export_csv), ('pdf', w._export_pdf)):
                    QFileDialog.getSaveFileName = lambda *a, ext=suffix: (str(output / ('ejemplo_revisado.' + ext)), '')
                    action(); check((output / ('ejemplo_revisado.' + suffix)).stat().st_size > 0, suffix + ' export through GUI')
                QFileDialog.getExistingDirectory = lambda *a: str(output)
                w._export_images(); check(any(output.glob('*_imagenes/*.png')), 'annotated images export through GUI')
                payload = json.loads((output / 'ejemplo_revisado.json').read_text(encoding='utf-8'))
                check(payload['summary']['class_counts_after_review'] == result.class_counts(), 'JSON counts match reviewed UI')
                check(any(d['status'] == 'rejected_by_review' for d in payload['detections']), 'export preserves rejected provenance')
                report['counts_after_review'] = result.class_counts()
                state['phase'] = 2
                w._set_paths(state['images'] * 10, 'cancel check')
                w._analyze_button.click()
            elif phase == 2:
                if w._progress.value() >= 1 and w._is_analyzing():
                    w._cancel_button.click(); state['phase'] = 3
                elif not w._is_analyzing(): raise AssertionError('Cancellation window not exercised')
            elif phase == 3:
                if w._thread is not None: return
                check(w._thread is None and w._worker is None, 'cancel returns without stranded thread')
                w.close(); check(not w.isVisible(), 'window closes')
                reopened = MainWindow(w._service); windows.append(reopened); reopened.show()
                state['phase'] = 4
            elif phase == 4:
                check(w.isVisible() and w._result is None, 'window reopens with clean state')
                w.grab().save(str(output / '04_reapertura.png'))
                check(not any(x['kind'] == 'critical' for x in report['messages']), 'no critical GUI errors')
                finish()
        except Exception:
            finish(traceback.format_exc())

    try:
        load_start = time.perf_counter(); provider = provider_factory()
        report['model_load_seconds'] = time.perf_counter() - load_start
        for name in notices:
            setattr(QMessageBox, name, lambda parent, title, message, kind=name: report['messages'].append({'kind': kind, 'title': title, 'message': message}))
        window = MainWindow(AnalysisService(provider)); windows.append(window); window.show()
        timer.timeout.connect(tick); timer.start()
        return app.exec()
    except Exception:
        finish(traceback.format_exc())
        return 3
