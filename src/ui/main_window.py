from src.processing.class_normalizer import class_display_name, normalize_class_name
from src.processing.aggregator import KNOWN_CLASSES
from pathlib import Path
import tempfile

from PySide6.QtCore import QSize, Qt, QThread, Signal, QEvent
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QLineEdit,
    QDialog, QFormLayout, QFrame, QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QProgressBar, QPushButton, QSplitter, QStatusBar,
    QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget)

from src.domain.models import ImageAnalysis, StudyResult, generate_patient_id
from src.interpretation.rule_engine import interpret_study
from src.reports.pdf_report import export_annotated_images, generate_pdf
from src.services.analysis_service import AnalysisService
from src.services.export_service import export_csv, export_json
from src.processing.preprocessing import preprocess_experimental
from src.ui.analysis_worker import AnalysisWorker
from src.ui.image_renderer import CLASS_COLORS, fit_pixmap, legend_html, render_analysis


PALETTES = {
    "light": {"bg":"#F3F6F8", "surface":"#FFFFFF", "surface2":"#E8EEF2", "text":"#172B3A", "muted":"#5D7180", "line":"#CEDAE1", "primary":"#005EB8", "hover":"#004B93", "soft":"#E3F0FB", "warning":"#FFF4CE", "warningText":"#684C00"},
    "dark": {"bg":"#0E1822", "surface":"#162533", "surface2":"#203342", "text":"#F2F7FA", "muted":"#AABBC7", "line":"#395062", "primary":"#2D8DD2", "hover":"#52A7E2", "soft":"#173E5E", "warning":"#403619", "warningText":"#FFD66B"},
}


def stylesheet(theme: str) -> str:
    p = PALETTES[theme]
    return f"""
    QMainWindow, QWidget {{ background:{p['bg']}; color:{p['text']}; font-family:'Segoe UI Variable','Segoe UI'; font-size:13px; }}
    QLabel, QCheckBox {{ background:transparent; border:none; }}
    QFrame#header, QFrame[card='true'] {{ background:{p['surface']}; border:1px solid {p['line']}; border-radius:12px; }}
    QLabel#brand {{ font-size:23px; font-weight:700; color:{p['text']}; }}
    QLabel#section {{ color:{p['text']}; font-size:14px; font-weight:700; }}
    QLabel#muted, QLabel#subtitle {{ color:{p['muted']}; }}
    QLabel#stage {{ color:{p['primary']}; background:transparent; font-weight:600; }}
    QPushButton {{ min-height:24px; background:{p['surface']}; color:{p['text']}; border:1px solid {p['line']}; border-radius:8px; padding:8px 13px; }}
    QPushButton:hover {{ background:{p['soft']}; border-color:{p['primary']}; }}
    QPushButton#primary {{ background:{p['primary']}; color:#FFFFFF; border-color:{p['primary']}; font-weight:700; }}
    QPushButton#primary:hover {{ background:{p['hover']}; }}
    QPushButton#quiet {{ background:transparent; border:0; color:{p['muted']}; }}
    QPushButton#icon {{ min-width:28px; max-width:28px; min-height:28px; padding:3px; border:0; border-radius:16px; background:transparent; font-size:17px; }}
    QPushButton#icon:hover {{ background:{p['soft']}; }}
    QPushButton:disabled {{ color:{p['muted']}; background:{p['surface2']}; border-color:{p['line']}; }}
    QLineEdit, QDoubleSpinBox, QListWidget, QTableWidget, QTextEdit, QComboBox {{ background:{p['surface']}; color:{p['text']}; border:1px solid {p['line']}; border-radius:8px; padding:5px; selection-background-color:{p['soft']}; selection-color:{p['text']}; }}
    QListWidget::item {{ padding:9px 5px; border-bottom:1px solid {p['line']}; }}
    QListWidget::item:selected {{ background:{p['soft']}; color:{p['text']}; }}
    QHeaderView::section {{ background:{p['surface2']}; color:{p['text']}; padding:8px; border:0; border-right:1px solid {p['line']}; font-weight:600; }}
    QLabel#warning {{ color:{p['warningText']}; background:{p['warning']}; border-radius:8px; padding:10px; }}
    QProgressBar {{ border:0; text-align:center; background:{p['surface2']}; color:{p['text']}; }}
    QProgressBar::chunk {{ background:{p['primary']}; }}
    QStatusBar {{ background:{p['surface']}; color:{p['muted']}; border-top:1px solid {p['line']}; }}
    """


class ThemeSwitch(QWidget):
    toggled = Signal(bool)

    def __init__(self) -> None:
        super().__init__(); self._dark = False; self.setFixedSize(66, 30)
        self.setCursor(Qt.PointingHandCursor); self.setToolTip("Cambiar entre modo claro y oscuro")

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._dark = not self._dark; self.toggled.emit(self._dark); self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self); painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen); painter.setBrush(QColor("#203342" if self._dark else "#DCE8F2"))
        painter.drawRoundedRect(self.rect(), 15, 15)
        x = 37 if self._dark else 3
        painter.setBrush(QColor("#FFFFFF")); painter.drawEllipse(x, 3, 24, 24)
        painter.setPen(QPen(QColor("#005EB8" if not self._dark else "#203342"), 1.6))
        if self._dark:
            painter.setBrush(QColor("#17323B")); painter.drawEllipse(x + 7, 8, 10, 12)
            painter.setBrush(QColor("#FFFFFF")); painter.setPen(Qt.NoPen); painter.drawEllipse(x + 11, 6, 9, 10)
        else:
            painter.setBrush(Qt.NoBrush); painter.drawEllipse(x + 8, 10, 8, 8)
            for dx, dy in ((12,5),(12,23),(5,14),(23,14)): painter.drawPoint(x + dx, dy)
        painter.end()


class ClassBarChart(QWidget):
    def __init__(self) -> None:
        super().__init__(); self._counts: dict[str, int] = {}; self.setMinimumHeight(190)

    def set_counts(self, counts: dict[str, int]) -> None:
        self._counts = dict(counts); self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self); painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(self.font()); maximum = max(self._counts.values(), default=1)
        width = max(40, self.width() - 150); y = 8
        for name, total in sorted(self._counts.items(), key=lambda item: item[1], reverse=True):
            label = class_display_name(name); painter.setPen(self.palette().text().color())
            painter.drawText(4, y + 15, label[:19]); bar_width = max(3, int(width * total / maximum))
            painter.setPen(Qt.NoPen); painter.setBrush(CLASS_COLORS.get(name, QColor("#31B7B2")))
            painter.drawRoundedRect(125, y + 3, bar_width, 14, 5, 5)
            painter.setPen(self.palette().text().color()); painter.drawText(132 + width, y + 15, str(total)); y += 25
        if not self._counts:
            painter.setPen(self.palette().text().color()); painter.drawText(self.rect(), Qt.AlignCenter, "Sin datos estadísticos")
        painter.end()


class ImageView(QGraphicsView):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(360, 280)
        self.setStyleSheet("background:#e9f0f2;border:1px solid #c3d8dd;border-radius:9px;color:#607b84;")
        self.setScene(QGraphicsScene(self)); self._item = QGraphicsPixmapItem(); self.scene().addItem(self._item)
        self.setDragMode(QGraphicsView.ScrollHandDrag); self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self._manual_zoom = False

    def show_pixmap(self, pixmap: QPixmap) -> None:
        self._item.setPixmap(pixmap); self.scene().setSceneRect(self._item.boundingRect())
        self.reset_view()

    def reset_view(self) -> None:
        self.resetTransform(); self.fitInView(self._item, Qt.KeepAspectRatio); self._manual_zoom = False

    def zoom(self, factor: float) -> None:
        self.scale(factor, factor); self._manual_zoom = True

    def wheelEvent(self, event) -> None:
        self.zoom(1.15 if event.angleDelta().y() > 0 else 1 / 1.15)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if not self._manual_zoom: self.reset_view()


class MainWindow(QMainWindow):
    def __init__(self, service: AnalysisService) -> None:
        super().__init__()
        self._service, self._selected_paths, self._source = service, [], ""
        self._result: StudyResult | None = None
        self._thread: QThread | None = None
        self._worker: AnalysisWorker | None = None
        self._close_when_finished = False
        self._selected_detection_index: int | None = None
        self._preprocess_temp = None
        self._active_variant = "original"
        self._last_original_result: StudyResult | None = None
        self._patient_id_value = generate_patient_id()
        self.setWindowTitle("VECTOR UroSight — Análisis asistido de sedimento urinario")
        self.resize(1440, 900)
        self.setMinimumSize(1120, 720)
        self.setAcceptDrops(True)
        self._theme = "light"
        self.setStyleSheet(stylesheet(self._theme))
        self._build_ui()
        for widget in self.findChildren(QWidget):
            widget.setAcceptDrops(True)
            widget.installEventFilter(self)

    def _build_ui(self) -> None:
        root = QWidget(); layout = QVBoxLayout(root); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)
        header = QFrame(objectName="header"); h = QHBoxLayout(header); h.setContentsMargins(24, 12, 24, 12)
        titles = QVBoxLayout(); brand = QLabel("VECTOR UroSight", objectName="brand"); titles.addWidget(brand)
        titles.addWidget(QLabel("Plataforma de apoyo al análisis de sedimento urinario", objectName="subtitle")); h.addLayout(titles); h.addStretch()
        self._provider_badge = QLabel(self._provider_text(), objectName="muted"); self._provider_badge.setToolTip("Modelo integrado en esta versión"); h.addWidget(self._provider_badge)
        h.addSpacing(16); self._theme_switch = ThemeSwitch(); self._theme_switch.toggled.connect(self._set_dark_theme); h.addWidget(self._theme_switch); layout.addWidget(header)

        splitter = QSplitter(); splitter.setChildrenCollapsible(False); splitter.setContentsMargins(14, 14, 14, 10)
        sidebar = QFrame(); sidebar.setProperty("card", "true"); side = QVBoxLayout(sidebar); side.setContentsMargins(14, 14, 14, 14); side.setSpacing(10)
        self._stage = QLabel("1 · Añada los campos", objectName="stage"); side.addWidget(self._stage)
        self._patient_name = QLineEdit(); self._patient_name.setPlaceholderText("Paciente (opcional)"); self._patient_name.setClearButtonEnabled(True); side.addWidget(self._patient_name)
        self._patient_id = QLabel(self._patient_id_value, objectName="muted"); self._patient_id.setToolTip("Identificador aleatorio; no contiene datos del paciente."); self._patient_id.hide(); self._folio = QLabel("NUEVO ESTUDIO", objectName="muted"); self._folio.hide()
        self._add_files_button = QPushButton("Seleccionar archivos")
        self._add_files_button.clicked.connect(self._select_images)
        side.addWidget(self._add_files_button)
        self._add_folder_button = QPushButton("Seleccionar carpeta")
        self._add_folder_button.clicked.connect(self._select_folder)
        side.addWidget(self._add_folder_button)
        self._files = QListWidget(); self._files.setIconSize(QSize(74, 54)); self._files.currentRowChanged.connect(self._select_analysis); side.addWidget(self._files)
        self._file_hint = QLabel("Arrastre aquí imágenes o una carpeta", objectName="muted"); self._file_hint.setAlignment(Qt.AlignCenter); self._file_hint.setWordWrap(True); side.addWidget(self._file_hint)
        self._analyze_button = QPushButton("Analizar estudio", objectName="primary"); self._analyze_button.setToolTip("Procesa todos los campos con el modelo local."); self._analyze_button.clicked.connect(self._analyze); self._analyze_button.setEnabled(False); side.addWidget(self._analyze_button)
        self._cancel_button = QPushButton("Cancelar análisis"); self._cancel_button.clicked.connect(self._cancel); self._cancel_button.hide(); side.addWidget(self._cancel_button); splitter.addWidget(sidebar)

        center = QFrame(); center.setProperty("card", "true"); center_layout = QVBoxLayout(center); center_layout.setContentsMargins(14, 14, 14, 14); center_layout.setSpacing(9)
        viewer_tools = QHBoxLayout(); self._legend = QLabel("Seleccione imágenes para comenzar", objectName="muted"); viewer_tools.addWidget(self._legend); viewer_tools.addStretch()
        self._view_mode = QComboBox(); self._view_mode.addItems(["Vista anotada", "Vista original"]); self._view_mode.currentIndexChanged.connect(self._refresh_view); viewer_tools.addWidget(self._view_mode)
        self._class_filter = QComboBox(); self._class_filter.addItem("Todas las clases"); self._class_filter.currentIndexChanged.connect(self._refresh_view); viewer_tools.addWidget(self._class_filter)
        settings = QPushButton("⚙", objectName="icon"); settings.setToolTip("Preferencias de análisis"); settings.clicked.connect(self._show_preferences); viewer_tools.addWidget(settings); center_layout.addLayout(viewer_tools)
        self._viewer = ImageView(); center_layout.addWidget(self._viewer, 3)
        self._field_details = QLabel("Seleccione un campo para consultar sus resultados.", objectName="muted"); self._field_details.setWordWrap(True); center_layout.addWidget(self._field_details)
        self._detections = QTableWidget(0, 7); self._detections.setHorizontalHeaderLabels(["Clase original", "Hallazgo", "Confianza", "Caja", "Estado", "Revisión", "Corrección"]); self._detections.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self._detections.setEditTriggers(QAbstractItemView.NoEditTriggers); center_layout.addWidget(self._detections, 1)
        self._review_panel = QWidget(); review_tools = QHBoxLayout(self._review_panel); review_tools.setContentsMargins(0, 0, 0, 0); self._review_status = QComboBox(); self._review_status.addItems(["correcta", "incorrecta", "clase_equivocada", "elemento_omitido"]); review_tools.addWidget(self._review_status); self._corrected_class = QComboBox(); self._corrected_class.setEditable(True); review_tools.addWidget(self._corrected_class); apply_review = QPushButton("Guardar revisión"); apply_review.clicked.connect(self._apply_review); review_tools.addWidget(apply_review); self._review_panel.hide(); center_layout.addWidget(self._review_panel)
        self._preferences = QDialog(self); self._preferences.setWindowTitle("Preferencias de análisis"); self._preferences.setMinimumWidth(410); preferences_layout = QVBoxLayout(self._preferences)
        self._annotations = QCheckBox("Mostrar anotaciones"); self._annotations.setChecked(True); self._annotations.toggled.connect(self._refresh_view); preferences_layout.addWidget(self._annotations)
        self._audit_mode = QCheckBox("Modo de auditoría"); self._audit_mode.toggled.connect(self._audit_toggled); preferences_layout.addWidget(self._audit_mode)
        threshold_form = QFormLayout(); self._threshold = QDoubleSpinBox(); self._threshold.setRange(0, 1); self._threshold.setSingleStep(.05); self._threshold.setDecimals(2); self._threshold.setValue(self._service.confidence_threshold); self._threshold.valueChanged.connect(self._threshold_changed); threshold_form.addRow("Umbral de confianza", self._threshold); preferences_layout.addLayout(threshold_form)
        self._experimental_preprocess = QCheckBox("Mejora experimental de imagen"); self._experimental_preprocess.setToolTip("CLAHE y reducción ligera de ruido; nunca modifica originales."); preferences_layout.addWidget(self._experimental_preprocess)
        close_preferences = QPushButton("Listo", objectName="primary"); close_preferences.clicked.connect(self._preferences.accept); preferences_layout.addWidget(close_preferences)
        splitter.addWidget(center)
        self._detections.cellClicked.connect(self._detection_selected)

        results = QFrame(); results.setProperty("card", "true"); results_layout = QVBoxLayout(results); results_layout.setContentsMargins(14, 14, 14, 14); results_layout.setSpacing(10); results_layout.addWidget(QLabel("Resultados", objectName="section"))
        cards = QGridLayout(); self._count_card = self._card(cards, "Hallazgos", 0, 0); self._confidence_card = self._card(cards, "Confianza media", 0, 1); self._time_card = self._card(cards, "Tiempo", 1, 0); self._images_card = self._card(cards, "Campos", 1, 1); results_layout.addLayout(cards)
        self._class_chart = ClassBarChart(); self._class_chart.setMaximumHeight(170); results_layout.addWidget(self._class_chart)
        self._summary = QTableWidget(0, 3); self._summary.setHorizontalHeaderLabels(["Clase", "Total", "Prom./campo"]); self._summary.hide()
        results_layout.addWidget(QLabel("Interpretación orientativa", objectName="section")); self._interpretation = QTextEdit(); self._interpretation.setReadOnly(True); self._interpretation.setPlaceholderText("La interpretación aparecerá al terminar el análisis."); results_layout.addWidget(self._interpretation, 1)
        warning = QLabel("USO ACADÉMICO · Confirme visualmente cada hallazgo. No sustituye el criterio profesional."); warning.setObjectName("warning"); warning.setWordWrap(True); results_layout.addWidget(warning)
        self._export_button = QPushButton("Exportar resultados", objectName="primary"); self._export_button.setEnabled(False)
        self._export_button.clicked.connect(self._show_export_options)
        results_layout.addWidget(self._export_button); splitter.addWidget(results)
        splitter.setSizes([235, 850, 355]); layout.addWidget(splitter, 1)
        self._progress = QProgressBar(); self._progress.hide(); layout.addWidget(self._progress)
        self.setStatusBar(QStatusBar()); self.statusBar().showMessage("Seleccione imágenes para comenzar.")
        self.setCentralWidget(root)
        self._audit_toggled(False)

    def _set_dark_theme(self, enabled: bool) -> None:
        self._theme = "dark" if enabled else "light"
        self.setStyleSheet(stylesheet(self._theme))
        self._viewer.setStyleSheet(f"background:{'#0B1419' if self._theme == 'dark' else '#E7EFF2'};border:1px solid {PALETTES[self._theme]['line']};border-radius:9px;")

    def _toggle_theme(self) -> None:
        self._theme_switch._dark = not self._theme_switch._dark
        self._theme_switch.update(); self._set_dark_theme(self._theme_switch._dark)

    def _show_preferences(self) -> None:
        self._preferences.open()

    def _set_stage(self, number: int, label: str) -> None:
        self._stage.setText(f"{number} · {label}")

    def _provider_text(self) -> str:
        return ("MODO DEMOSTRACIÓN - RESULTADOS SIMULADOS" if self._service.is_simulated
                else "YOLO11s")

    @staticmethod
    def _card(layout: QGridLayout, title: str, row: int, col: int) -> QLabel:
        frame = QFrame(); frame.setProperty("card", "true"); box = QVBoxLayout(frame); box.addWidget(QLabel(title, objectName="muted")); value = QLabel("—"); value.setStyleSheet("font-size:20px;font-weight:700;"); box.addWidget(value); layout.addWidget(frame, row, col); return value

    def _is_analyzing(self) -> bool:
        return bool(self._thread and self._thread.isRunning())

    def _can_drop(self, mime) -> bool:
        return not self._is_analyzing() and any(
            url.isLocalFile() and (Path(url.toLocalFile()).is_dir() or
            Path(url.toLocalFile()).suffix.lower() in self._service.SUPPORTED_EXTENSIONS)
            for url in mime.urls())

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.DragEnter, QEvent.DragMove, QEvent.Drop) and event.mimeData().hasUrls():
            if self._can_drop(event.mimeData()):
                if event.type() == QEvent.Drop:
                    self.dropEvent(event)
                else:
                    event.acceptProposedAction()
            else:
                event.ignore()
            return True
        return super().eventFilter(watched, event)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._can_drop(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        self.dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        if not self._can_drop(event.mimeData()):
            event.ignore()
            return
        paths: list[Path] = []
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue
            path = Path(url.toLocalFile()).resolve()
            paths.extend(self._service.collect_folder(path) if path.is_dir() else [path])
        if paths:
            self._set_paths(paths, "Arrastrar y soltar")
        else:
            self.statusBar().showMessage("La carpeta no contiene imágenes compatibles.")
        event.acceptProposedAction()

    def _show_export_options(self) -> None:
        if not self._result:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Exportar resultados")
        dialog.setMinimumWidth(380)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        layout.addWidget(QLabel("Elija qué desea guardar", objectName="section"))
        for title, description, callback in (
            ("Guardar reporte PDF", "Resumen del estudio y evidencia visual.", self._export_pdf),
            ("Guardar imágenes anotadas", "Imágenes con las detecciones revisadas.", self._export_images),
            ("Guardar estadísticas CSV", "Conteos para consultar en una hoja de cálculo.", self._export_csv),
        ):
            button = QPushButton(title)
            button.clicked.connect(lambda checked=False, action=callback: (dialog.accept(), action()))
            layout.addWidget(button)
            layout.addWidget(QLabel(description, objectName="muted"))
        cancel = QPushButton("Cancelar")
        cancel.clicked.connect(dialog.reject)
        layout.addWidget(cancel)
        dialog.exec()

    def _select_images(self) -> None:
        if self._is_analyzing(): return
        names, _ = QFileDialog.getOpenFileNames(self, "Seleccionar imágenes", "", "Imágenes (*.jpg *.jpeg *.png *.bmp *.tif *.tiff)")
        if names: self._set_paths([Path(name) for name in names], "Selección de archivos")

    def _select_folder(self) -> None:
        if self._is_analyzing(): return
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
        if folder:
            paths = self._service.collect_folder(Path(folder))
            if not paths: QMessageBox.information(self, "Carpeta vacía", "La carpeta no contiene imágenes compatibles.")
            else: self._set_paths(paths, folder)

    def _set_paths(self, paths: list[Path], source: str) -> None:
        if self._is_analyzing(): return
        accepted, rejected = [], []
        for path in dict.fromkeys(paths):
            valid, reason = self._service.validate_image(path)
            (accepted if valid else rejected).append(path if valid else f"{path.name}: {reason}")
        self._selected_paths, self._source, self._result = accepted, source, None; self._files.clear(); self._export_button.setEnabled(False)
        self._analyze_button.setEnabled(bool(accepted)); self._set_stage(2 if accepted else 1, "Listo para analizar" if accepted else "Preparar estudio")
        self._patient_id_value = generate_patient_id(); self._patient_id.setText(self._patient_id_value)
        for path in accepted:
            item = QListWidgetItem(QIcon(str(path)), path.name); item.setToolTip(str(path)); self._files.addItem(item)
        if accepted: self._files.setCurrentRow(0); self._show_original(accepted[0])
        self.statusBar().showMessage(f"{len(accepted)} imagen(es) listas." + (f" {len(rejected)} rechazadas." if rejected else ""))
        if rejected: QMessageBox.warning(self, "Archivos omitidos", "No se cargaron:\n" + "\n".join(map(str, rejected[:8])))

    def _analyze(self) -> None:
        if not self._selected_paths: QMessageBox.information(self, "Sin imágenes", "Cargue al menos una imagen válida."); return
        if self._thread and self._thread.isRunning(): return
        analysis_paths = self._selected_paths; source = self._source; self._active_variant = "original"
        if self._experimental_preprocess.isChecked():
            if self._preprocess_temp: self._preprocess_temp.cleanup()
            self._preprocess_temp = tempfile.TemporaryDirectory(prefix="vector_urosight_preprocessed_")
            folder = Path(self._preprocess_temp.name)
            try: analysis_paths = [preprocess_experimental(path, folder/path.name) for path in self._selected_paths]
            except Exception as exc: QMessageBox.critical(self, "Preprocesamiento no disponible", str(exc)); return
            self._active_variant = "preprocesada_experimental"; source = f"{self._source} · PREPROCESAMIENTO EXPERIMENTAL"
        self._thread = QThread(self); self._worker = AnalysisWorker(self._service, analysis_paths, source); self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run); self._worker.progress.connect(self._on_progress); self._worker.completed.connect(self._on_completed); self._worker.failed.connect(lambda message: QMessageBox.critical(self, "Error de análisis", message)); self._worker.finished.connect(self._finish_worker); self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._thread_finished)
        self._add_files_button.setEnabled(False); self._add_folder_button.setEnabled(False)
        self._export_button.setEnabled(False)
        self._analyze_button.setEnabled(False); self._cancel_button.show(); self._progress.setRange(0, len(self._selected_paths)); self._progress.setValue(0); self._progress.show(); self._thread.start()
        self._set_stage(2, "Analizando campos")

    def _cancel(self) -> None:
        if self._worker: self._worker.cancel(); self.statusBar().showMessage("Cancelación solicitada…")

    def _on_progress(self, done: int, total: int, name: str) -> None:
        self._progress.setMaximum(total); self._progress.setValue(done); self.statusBar().showMessage(f"Procesando {done}/{total}: {name}")

    def _finish_worker(self) -> None:
        self._analyze_button.setEnabled(True); self._cancel_button.hide()

    def _thread_finished(self) -> None:
        self._add_files_button.setEnabled(True); self._add_folder_button.setEnabled(True)
        self._export_button.setEnabled(self._result is not None)
        if self._close_when_finished:
            self._close_when_finished = False
            self.close()

    def _on_completed(self, result: StudyResult) -> None:
        result.patient_name = self._patient_name.text().strip()
        result.patient_id = self._patient_id_value
        for image in result.images: image.processing_variant = self._active_variant
        if self._active_variant == "original": self._last_original_result = result
        self._result = result; self._folio.setText(f"FOLIO {result.study_id}"); self._export_button.setEnabled(True)
        self._set_stage(3, "Revisar hallazgos")
        result.confidence_threshold = self._threshold.value()
        self._update_study_results()
        self._files.setCurrentRow(0); self._select_analysis(0); self.statusBar().showMessage(f"Análisis finalizado. {len(result.failed_images)} campo(s) con error.")
        if self._active_variant != "original" and self._last_original_result:
            delta = sum(result.class_counts().values()) - sum(self._last_original_result.class_counts().values())
            self.statusBar().showMessage(f"Comparación experimental finalizada: {delta:+d} detecciones frente al análisis original. Resultados no combinados.")

    def _update_study_results(self) -> None:
        if not self._result: return
        result = self._result; counts = result.class_counts(); averages = result.averages_per_image(); self._summary.setRowCount(len(counts))
        for row, (name, total) in enumerate(sorted(counts.items())):
            for col, value in enumerate((class_display_name(name), str(total), f"{averages[name]:.2f}")): self._summary.setItem(row, col, QTableWidgetItem(value))
        self._class_chart.set_counts(counts)
        self._count_card.setText(str(sum(counts.values()))); self._confidence_card.setText(f"{result.average_confidence():.1%}")
        self._time_card.setText("Simulado" if result.is_simulated else f"{result.total_inference_ms():.1f} ms"); self._images_card.setText(f"{len(result.successful_images)}/{len(result.images)}")
        self._interpretation.setPlainText("\n\n".join(interpret_study(result)))
        classes = sorted({d.class_name for image in result.successful_images for d in image.detections})
        self._legend.setText(legend_html(set(classes))); self._corrected_class.clear()
        for name in sorted(KNOWN_CLASSES | set(classes)):
            self._corrected_class.addItem(class_display_name(name), name)
        current = self._class_filter.currentData()
        self._class_filter.blockSignals(True); self._class_filter.clear()
        self._class_filter.addItem("Todas las clases", None)
        for name in classes:
            self._class_filter.addItem(class_display_name(name), name)
        self._class_filter.setCurrentIndex(max(0, self._class_filter.findData(current)))
        self._class_filter.blockSignals(False)

    def _threshold_changed(self, value: float) -> None:
        if self._result:
            self._result.confidence_threshold = value; self._selected_detection_index = None
            self._update_study_results(); self._refresh_view()

    def _audit_toggled(self, enabled: bool) -> None:
        if self._result: self._result.audit_mode = enabled
        for column in (0, 3, 4, 5, 6): self._detections.setColumnHidden(column, not enabled)
        if not enabled: self._review_panel.hide()
        self._refresh_view()

    def _select_analysis(self, row: int) -> None:
        if row < 0: return
        if self._result and row < len(self._result.images): self._display_analysis(self._result.images[row])
        elif row < len(self._selected_paths): self._show_original(self._selected_paths[row])

    def _show_original(self, path: Path) -> None:
        self._viewer.show_pixmap(QPixmap(str(path)))

    def _reset_view(self) -> None:
        self._selected_detection_index = None; self._refresh_view(); self._viewer.reset_view()

    def _refresh_view(self) -> None:
        self._select_analysis(self._files.currentRow())

    def _display_analysis(self, analysis: ImageAnalysis) -> None:
        if analysis.error:
            self._viewer.show_pixmap(QPixmap()); self._field_details.setText(f"No se pudo procesar {analysis.image_path.name}: {analysis.error}"); self._detections.setRowCount(0); return
        selected = self._class_filter.currentData(); visible = None if selected is None else {selected}
        annotated = self._view_mode.currentIndex() == 0 and self._annotations.isChecked(); threshold = self._result.confidence_threshold if self._result else 0
        render_threshold = 0.0 if self._audit_mode.isChecked() else threshold
        self._viewer.show_pixmap(render_analysis(analysis, visible, annotated, render_threshold, self._selected_detection_index)); indexed = [(i, d) for i, d in enumerate(analysis.detections) if (self._audit_mode.isChecked() or d.confidence >= threshold) and (visible is None or d.class_name in visible)]; self._detections.setRowCount(len(indexed))
        self._detections.setProperty("detection_indices", [i for i, _ in indexed])
        for row, (_, d) in enumerate(indexed):
            values = (d.raw_class or d.class_name, class_display_name(d.class_name), f"{d.confidence:.1%}", f"{d.bbox.x:.0f}, {d.bbox.y:.0f}, {d.bbox.width:.0f}, {d.bbox.height:.0f}", "aceptada" if d.confidence >= threshold else "descartada por umbral", d.human_review, d.corrected_class)
            for col, value in enumerate(values): self._detections.setItem(row, col, QTableWidgetItem(value))
        accepted = analysis.accepted_detections(threshold); avg = sum(d.confidence for d in accepted)/len(accepted) if accepted else 0
        counts: dict[str, int] = {}
        for detection in accepted: counts[detection.class_name] = counts.get(detection.class_name, 0) + 1
        count_text = ", ".join(f"{class_display_name(name)}: {total}" for name, total in sorted(counts.items())) or "sin detecciones"
        quality = analysis.quality; quality_text = "Sin evaluación"
        if quality: quality_text = f"{quality.status} · {quality.width}×{quality.height} · brillo {quality.brightness:.0f} · contraste {quality.contrast:.0f} · nitidez {quality.sharpness:.0f}"
        warnings = list(analysis.warnings) + (list(quality.warnings) if quality else [])
        time_text = "tiempo simulado" if self._result and self._result.is_simulated else f"{analysis.inference_ms or 0:.1f} ms"
        self._field_details.setText(f"{analysis.image_path.name} · Estado: correcto · {len(accepted)} aceptadas · {len(analysis.hidden_detections(threshold))} ocultas · confianza {avg:.1%} · {time_text}\nConteos: {count_text}\nCalidad: {quality_text}" + ("\nAdvertencias: " + "; ".join(warnings) if warnings else ""))

    def _detection_selected(self, row: int, _column: int) -> None:
        indices = self._detections.property("detection_indices") or []
        if row < len(indices):
            self._selected_detection_index = indices[row]; self._refresh_view(); self._detections.selectRow(row)
            self._review_panel.setVisible(self._audit_mode.isChecked())
            if self._result and 0 <= self._files.currentRow() < len(self._result.images):
                box = self._result.images[self._files.currentRow()].detections[self._selected_detection_index].bbox
                self._viewer.centerOn(box.x, box.y)

    def _review_class_value(self) -> str:
        text = self._corrected_class.currentText().strip()
        index = self._corrected_class.findText(text)
        return self._corrected_class.itemData(index) if index >= 0 else normalize_class_name(text)

    def _apply_review(self) -> None:
        if not self._result or self._selected_detection_index is None: return
        image = self._result.images[self._files.currentRow()]; status = self._review_status.currentText()
        if status == "elemento_omitido":
            image.omitted_elements.append({"status": status, "class": self._review_class_value()})
        else:
            detection = image.detections[self._selected_detection_index]; detection.human_review = status
            detection.corrected_class = self._review_class_value() if status == "clase_equivocada" else ""
        self._update_study_results(); self._refresh_view(); self.statusBar().showMessage("Revisión humana guardada en el estudio; use Exportar para persistirla.")

    def _export_file(self, label: str, suffix: str, file_filter: str, writer) -> None:
        if not self._result: return
        filename, _ = QFileDialog.getSaveFileName(self, label, f"VECTOR_UroSight_{self._result.study_id}{suffix}", file_filter)
        if not filename: return
        path = Path(filename).with_suffix(suffix)
        try:
            writer(self._result, path); self._set_stage(4, "Exportación completada")
            self.statusBar().showMessage(f"Archivo exportado: {path}")
        except Exception as exc: QMessageBox.critical(self, "No se pudo exportar", str(exc))

    def _export(self) -> None:
        self._export_pdf()

    def _export_pdf(self) -> None:
        self._export_file("Guardar reporte clínico", ".pdf", "PDF (*.pdf)", generate_pdf)

    def _export_csv(self) -> None:
        self._export_file("Guardar estadísticas", ".csv", "CSV (*.csv)", export_csv)

    def _export_json(self) -> None:
        self._export_file("Guardar sesión completa", ".json", "JSON (*.json)", export_json)

    def _export_images(self) -> None:
        if not self._result: return
        selected = QFileDialog.getExistingDirectory(self, "Carpeta para imágenes anotadas")
        if not selected: return
        folder = Path(selected) / f"VECTOR_UroSight_{self._result.study_id}_imagenes"
        try:
            paths = export_annotated_images(self._result, folder)
            self._set_stage(4, "Exportación completada")
            self.statusBar().showMessage(f"{len(paths)} imágenes anotadas exportadas en: {folder}")
        except Exception as exc: QMessageBox.critical(self, "No se pudieron exportar las imágenes", str(exc))

    def closeEvent(self, event) -> None:
        if self._thread and self._thread.isRunning():
            if self._worker: self._worker.cancel()
            self._close_when_finished = True
            self.statusBar().showMessage("Finalizando el campo en curso antes de cerrar…")
            event.ignore()
            return
        if self._preprocess_temp: self._preprocess_temp.cleanup()
        event.accept()
