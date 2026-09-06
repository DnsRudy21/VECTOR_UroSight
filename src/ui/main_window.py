from pathlib import Path
import tempfile

from PySide6.QtCore import QSize, Qt, QThread, Signal
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QLineEdit,
    QFrame, QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QListWidget, QListWidgetItem,
    QMainWindow, QMenu, QMessageBox, QProgressBar, QPushButton, QSplitter, QStatusBar, QTabWidget,
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
    "light": {"bg":"#F4F7F9", "surface":"#FFFFFF", "surface2":"#EAF2F5", "text":"#17323B", "muted":"#607780", "line":"#D4E1E5", "primary":"#087F8C", "hover":"#076B76", "soft":"#DDF1F1", "warning":"#FFF5D9", "warningText":"#77550A"},
    "dark": {"bg":"#101A20", "surface":"#17252C", "surface2":"#1D3038", "text":"#EAF3F5", "muted":"#A6BBC2", "line":"#334A54", "primary":"#31B7B2", "hover":"#45C9C3", "soft":"#203E43", "warning":"#3D321A", "warningText":"#F3CF72"},
}


def stylesheet(theme: str) -> str:
    p = PALETTES[theme]
    return f"""
    QMainWindow, QWidget {{ background:{p['bg']}; color:{p['text']}; font-family:'Segoe UI'; font-size:13px; }}
    QFrame#header, QFrame[card='true'] {{ background:{p['surface']}; border:1px solid {p['line']}; border-radius:12px; }}
    QLabel#brand {{ font-size:23px; font-weight:700; color:{p['text']}; }}
    QLabel#section {{ color:{p['text']}; font-size:14px; font-weight:700; }}
    QLabel#muted, QLabel#subtitle {{ color:{p['muted']}; }}
    QLabel#stage {{ color:{p['primary']}; background:{p['soft']}; padding:6px 12px; border-radius:12px; font-weight:700; }}
    QPushButton {{ min-height:24px; background:{p['surface']}; color:{p['text']}; border:1px solid {p['line']}; border-radius:8px; padding:8px 13px; }}
    QPushButton:hover {{ background:{p['soft']}; border-color:{p['primary']}; }}
    QPushButton#primary {{ background:{p['primary']}; color:#FFFFFF; border-color:{p['primary']}; font-weight:700; }}
    QPushButton#primary:hover {{ background:{p['hover']}; }}
    QPushButton#quiet {{ background:transparent; border:0; color:{p['muted']}; }}
    QPushButton:disabled {{ color:{p['muted']}; background:{p['surface2']}; border-color:{p['line']}; }}
    QLineEdit, QDoubleSpinBox, QListWidget, QTableWidget, QTextEdit, QComboBox {{ background:{p['surface']}; color:{p['text']}; border:1px solid {p['line']}; border-radius:8px; padding:5px; selection-background-color:{p['soft']}; selection-color:{p['text']}; }}
    QListWidget::item {{ padding:9px 5px; border-bottom:1px solid {p['line']}; }}
    QListWidget::item:selected {{ background:{p['soft']}; color:{p['text']}; }}
    QHeaderView::section {{ background:{p['surface2']}; color:{p['text']}; padding:8px; border:0; border-right:1px solid {p['line']}; font-weight:600; }}
    QTabWidget::pane {{ border:1px solid {p['line']}; border-radius:9px; background:{p['surface']}; }}
    QTabBar::tab {{ background:{p['surface2']}; color:{p['muted']}; padding:9px 15px; margin-right:2px; border-top-left-radius:7px; border-top-right-radius:7px; }}
    QTabBar::tab:selected {{ background:{p['surface']}; color:{p['primary']}; font-weight:700; }}
    QLabel#warning {{ color:{p['warningText']}; background:{p['warning']}; border-radius:8px; padding:10px; }}
    QProgressBar {{ border:0; text-align:center; background:{p['surface2']}; color:{p['text']}; }}
    QProgressBar::chunk {{ background:{p['primary']}; }}
    QStatusBar {{ background:{p['surface']}; color:{p['muted']}; border-top:1px solid {p['line']}; }}
    """


class ThemeSwitch(QWidget):
    toggled = Signal(bool)

    def __init__(self) -> None:
        super().__init__(); self._dark = False; self.setFixedSize(54, 28)
        self.setCursor(Qt.PointingHandCursor); self.setToolTip("Cambiar entre modo claro y oscuro")

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._dark = not self._dark; self.toggled.emit(self._dark); self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self); painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen); painter.setBrush(QColor("#31B7B2" if self._dark else "#AFC3CA"))
        painter.drawRoundedRect(self.rect(), 14, 14)
        painter.setBrush(QColor("#FFFFFF")); x = 28 if self._dark else 3
        painter.drawEllipse(x, 3, 22, 22); painter.end()


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
            label = name.replace("_", " ").title(); painter.setPen(self.palette().text().color())
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

    def _build_ui(self) -> None:
        root = QWidget(); layout = QVBoxLayout(root); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)
        header = QFrame(objectName="header"); h = QHBoxLayout(header); h.setContentsMargins(24, 12, 24, 12)
        titles = QVBoxLayout(); brand = QLabel("VECTOR UroSight", objectName="brand"); titles.addWidget(brand)
        titles.addWidget(QLabel("Plataforma de apoyo al análisis de sedimento urinario", objectName="subtitle")); h.addLayout(titles); h.addStretch()
        self._provider_badge = QLabel(self._provider_text(), objectName="muted"); h.addWidget(self._provider_badge)
        h.addSpacing(18); h.addWidget(QLabel("Claro", objectName="muted")); self._theme_switch = ThemeSwitch(); self._theme_switch.toggled.connect(self._set_dark_theme); h.addWidget(self._theme_switch); h.addWidget(QLabel("Oscuro", objectName="muted")); layout.addWidget(header)

        splitter = QSplitter(); splitter.setChildrenCollapsible(False); splitter.setContentsMargins(14, 14, 14, 10)
        sidebar = QFrame(); sidebar.setProperty("card", "true"); side = QVBoxLayout(sidebar); side.setContentsMargins(14, 14, 14, 14); side.setSpacing(10)
        side.addWidget(QLabel("Nuevo estudio", objectName="section")); self._stage = QLabel("1 · Cargue los campos", objectName="stage"); side.addWidget(self._stage); side.addWidget(QLabel("Paciente (opcional)", objectName="muted"))
        self._patient_name = QLineEdit(); self._patient_name.setPlaceholderText("Nombre completo"); side.addWidget(self._patient_name)
        self._patient_id = QLabel(self._patient_id_value, objectName="muted"); self._patient_id.setToolTip("Identificador aleatorio; no contiene datos del paciente."); side.addWidget(self._patient_id); self._folio = QLabel("NUEVO ESTUDIO", objectName="muted"); side.addWidget(self._folio)
        load_row = QHBoxLayout(); images = QPushButton("＋ Imágenes"); images.clicked.connect(self._select_images); folder = QPushButton("＋ Carpeta"); folder.clicked.connect(self._select_folder); load_row.addWidget(images); load_row.addWidget(folder); side.addLayout(load_row)
        side.addWidget(QLabel("Campos cargados", objectName="section"))
        self._files = QListWidget(); self._files.setIconSize(QSize(74, 54)); self._files.currentRowChanged.connect(self._select_analysis); side.addWidget(self._files)
        self._file_hint = QLabel("Arrastre aquí imágenes o una carpeta", objectName="muted"); self._file_hint.setAlignment(Qt.AlignCenter); self._file_hint.setWordWrap(True); side.addWidget(self._file_hint)
        self._analyze_button = QPushButton("Analizar estudio", objectName="primary"); self._analyze_button.setToolTip("Procesa todos los campos con el modelo local."); self._analyze_button.clicked.connect(self._analyze); self._analyze_button.setEnabled(False); side.addWidget(self._analyze_button)
        self._cancel_button = QPushButton("Cancelar análisis"); self._cancel_button.clicked.connect(self._cancel); self._cancel_button.hide(); side.addWidget(self._cancel_button); splitter.addWidget(sidebar)

        center = QFrame(); center.setProperty("card", "true"); center_layout = QVBoxLayout(center); center_layout.setContentsMargins(14, 14, 14, 14); center_layout.setSpacing(9)
        viewer_tools = QHBoxLayout(); viewer_tools.addWidget(QLabel("Campo seleccionado", objectName="section")); viewer_tools.addStretch()
        self._view_mode = QComboBox(); self._view_mode.addItems(["Vista anotada", "Vista original"]); self._view_mode.currentIndexChanged.connect(self._refresh_view); viewer_tools.addWidget(self._view_mode)
        self._class_filter = QComboBox(); self._class_filter.addItem("Todas las clases"); self._class_filter.currentIndexChanged.connect(self._refresh_view); viewer_tools.addWidget(self._class_filter); center_layout.addLayout(viewer_tools)
        zoom_tools = QHBoxLayout(); self._legend = QLabel("Sin hallazgos para mostrar", objectName="muted"); zoom_tools.addWidget(self._legend); zoom_tools.addStretch()
        for text, factor in (("−", .8), ("+", 1.25)):
            button = QPushButton(text); button.setFixedWidth(38); button.clicked.connect(lambda _=False, value=factor: self._viewer.zoom(value)); zoom_tools.addWidget(button)
        reset = QPushButton("Ajustar"); reset.clicked.connect(self._reset_view); zoom_tools.addWidget(reset); center_layout.addLayout(zoom_tools)
        self._viewer = ImageView(); center_layout.addWidget(self._viewer, 3)
        self._field_details = QLabel("Seleccione un campo para consultar sus resultados.", objectName="muted"); self._field_details.setWordWrap(True); center_layout.addWidget(self._field_details)
        tabs = QTabWidget()
        findings = QWidget(); findings_layout = QVBoxLayout(findings); findings_layout.setContentsMargins(8, 8, 8, 8)
        self._detections = QTableWidget(0, 7); self._detections.setHorizontalHeaderLabels(["Clase original", "Clase normalizada", "Confianza", "Caja", "Estado", "Revisión", "Corrección"]); self._detections.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self._detections.setEditTriggers(QAbstractItemView.NoEditTriggers); center_layout.addWidget(self._detections, 1)
        review_tools = QHBoxLayout(); review_tools.addWidget(QLabel("Revisión humana:")); self._review_status = QComboBox(); self._review_status.addItems(["correcta", "incorrecta", "clase_equivocada", "elemento_omitido"]); review_tools.addWidget(self._review_status); self._corrected_class = QComboBox(); self._corrected_class.setEditable(True); review_tools.addWidget(self._corrected_class); apply_review = QPushButton("Guardar revisión"); apply_review.clicked.connect(self._apply_review); review_tools.addWidget(apply_review)
        center_layout.removeWidget(self._detections); findings_layout.addWidget(self._detections); findings_layout.addLayout(review_tools); tabs.addTab(findings, "Hallazgos")
        advanced = QWidget(); advanced_layout = QVBoxLayout(advanced); advanced_layout.setContentsMargins(16, 14, 16, 14)
        self._annotations = QCheckBox("Mostrar anotaciones sobre la imagen"); self._annotations.setChecked(True); self._annotations.toggled.connect(self._refresh_view); advanced_layout.addWidget(self._annotations)
        self._audit_mode = QCheckBox("Mostrar detecciones descartadas (auditoría)"); self._audit_mode.toggled.connect(self._audit_toggled); advanced_layout.addWidget(self._audit_mode)
        threshold_row = QHBoxLayout(); threshold_row.addWidget(QLabel("Umbral de confianza")); self._threshold = QDoubleSpinBox(); self._threshold.setRange(0, 1); self._threshold.setSingleStep(.05); self._threshold.setDecimals(2); self._threshold.setValue(self._service.confidence_threshold); self._threshold.valueChanged.connect(self._threshold_changed); threshold_row.addWidget(self._threshold); threshold_row.addStretch(); advanced_layout.addLayout(threshold_row)
        self._experimental_preprocess = QCheckBox("Aplicar mejora experimental de imagen antes del análisis"); self._experimental_preprocess.setToolTip("CLAHE y reducción ligera de ruido; nunca modifica originales."); advanced_layout.addWidget(self._experimental_preprocess); advanced_layout.addStretch(); tabs.addTab(advanced, "Opciones avanzadas")
        center_layout.addWidget(tabs, 2); splitter.addWidget(center)
        self._detections.cellClicked.connect(self._detection_selected)

        results = QFrame(); results.setProperty("card", "true"); results_layout = QVBoxLayout(results); results_layout.setContentsMargins(14, 14, 14, 14); results_layout.setSpacing(10); results_layout.addWidget(QLabel("Resultados", objectName="section"))
        result_tabs = QTabWidget(); overview = QWidget(); overview_layout = QVBoxLayout(overview); overview_layout.setContentsMargins(8, 10, 8, 8)
        cards = QGridLayout(); self._count_card = self._card(cards, "Detecciones", 0, 0); self._confidence_card = self._card(cards, "Score promedio", 0, 1); self._time_card = self._card(cards, "Tiempo total", 1, 0); self._images_card = self._card(cards, "Campos procesados", 1, 1); overview_layout.addLayout(cards)
        overview_layout.addWidget(QLabel("Interpretación orientativa", objectName="section")); self._interpretation = QTextEdit(); self._interpretation.setReadOnly(True); self._interpretation.setPlaceholderText("Los hallazgos aparecerán al terminar el análisis."); overview_layout.addWidget(self._interpretation); result_tabs.addTab(overview, "Resumen")
        statistics = QWidget(); statistics_layout = QVBoxLayout(statistics); statistics_layout.setContentsMargins(8, 10, 8, 8); self._class_chart = ClassBarChart(); statistics_layout.addWidget(self._class_chart)
        self._summary = QTableWidget(0, 3); self._summary.setHorizontalHeaderLabels(["Clase", "Total", "Prom./campo"]); self._summary.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self._summary.setEditTriggers(QAbstractItemView.NoEditTriggers); statistics_layout.addWidget(self._summary); result_tabs.addTab(statistics, "Estadísticas"); results_layout.addWidget(result_tabs, 1)
        warning = QLabel("USO ACADÉMICO · Confirme visualmente cada hallazgo. No sustituye el criterio profesional."); warning.setObjectName("warning"); warning.setWordWrap(True); results_layout.addWidget(warning)
        self._export_button = QPushButton("Exportar ▾", objectName="primary"); self._export_button.setEnabled(False)
        export_menu = QMenu(self._export_button); export_menu.addAction("Reporte clínico PDF", self._export_pdf); export_menu.addAction("Imágenes anotadas", self._export_images); export_menu.addSeparator(); export_menu.addAction("Estadísticas CSV", self._export_csv); export_menu.addAction("Sesión completa JSON", self._export_json); self._export_button.setMenu(export_menu); results_layout.addWidget(self._export_button); splitter.addWidget(results)
        splitter.setSizes([255, 820, 350]); layout.addWidget(splitter, 1)
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

    def _set_stage(self, number: int, label: str) -> None:
        self._stage.setText(f"{number} · {label}")

    def _provider_text(self) -> str:
        return ("MODO DEMOSTRACIÓN - RESULTADOS SIMULADOS" if self._service.is_simulated
                else "Motor de análisis · YOLO11s")

    @staticmethod
    def _card(layout: QGridLayout, title: str, row: int, col: int) -> QLabel:
        frame = QFrame(); frame.setProperty("card", "true"); box = QVBoxLayout(frame); box.addWidget(QLabel(title, objectName="muted")); value = QLabel("—"); value.setStyleSheet("font-size:20px;font-weight:700;"); box.addWidget(value); layout.addWidget(frame, row, col); return value

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls(): event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        paths: list[Path] = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile()); paths.extend(self._service.collect_folder(path) if path.is_dir() else [path])
        self._set_paths(paths, "Arrastrar y soltar")

    def _select_images(self) -> None:
        names, _ = QFileDialog.getOpenFileNames(self, "Seleccionar imágenes", "", "Imágenes (*.jpg *.jpeg *.png *.bmp *.tif *.tiff)")
        if names: self._set_paths([Path(name) for name in names], "Selección de archivos")

    def _select_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
        if folder:
            paths = self._service.collect_folder(Path(folder))
            if not paths: QMessageBox.information(self, "Carpeta vacía", "La carpeta no contiene imágenes compatibles.")
            else: self._set_paths(paths, folder)

    def _set_paths(self, paths: list[Path], source: str) -> None:
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
        self._analyze_button.setEnabled(False); self._cancel_button.show(); self._progress.setRange(0, len(self._selected_paths)); self._progress.setValue(0); self._progress.show(); self._thread.start()
        self._set_stage(2, "Analizando campos")

    def _cancel(self) -> None:
        if self._worker: self._worker.cancel(); self.statusBar().showMessage("Cancelación solicitada…")

    def _on_progress(self, done: int, total: int, name: str) -> None:
        self._progress.setMaximum(total); self._progress.setValue(done); self.statusBar().showMessage(f"Procesando {done}/{total}: {name}")

    def _finish_worker(self) -> None:
        self._analyze_button.setEnabled(True); self._cancel_button.hide()

    def _thread_finished(self) -> None:
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
            for col, value in enumerate((name.replace("_", " ").title(), str(total), f"{averages[name]:.2f}")): self._summary.setItem(row, col, QTableWidgetItem(value))
        self._class_chart.set_counts(counts)
        self._count_card.setText(str(sum(counts.values()))); self._confidence_card.setText(f"{result.average_confidence():.1%}")
        self._time_card.setText("Simulado" if result.is_simulated else f"{result.total_inference_ms():.1f} ms"); self._images_card.setText(f"{len(result.successful_images)}/{len(result.images)}")
        self._interpretation.setPlainText("\n\n".join(interpret_study(result)))
        classes = sorted({d.class_name for image in result.successful_images for d in image.detections})
        self._legend.setText(legend_html(set(classes))); self._corrected_class.clear(); self._corrected_class.addItems(classes)
        current = self._class_filter.currentText(); self._class_filter.blockSignals(True); self._class_filter.clear(); self._class_filter.addItem("Todas las clases"); self._class_filter.addItems(classes); self._class_filter.setCurrentText(current if current in classes else "Todas las clases"); self._class_filter.blockSignals(False)

    def _threshold_changed(self, value: float) -> None:
        if self._result:
            self._result.confidence_threshold = value; self._selected_detection_index = None
            self._update_study_results(); self._refresh_view()

    def _audit_toggled(self, enabled: bool) -> None:
        if self._result: self._result.audit_mode = enabled
        for column in (0, 4, 5, 6): self._detections.setColumnHidden(column, not enabled)
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
        selected = self._class_filter.currentText(); visible = None if selected == "Todas las clases" else {selected}
        annotated = self._view_mode.currentIndex() == 0 and self._annotations.isChecked(); threshold = self._result.confidence_threshold if self._result else 0
        render_threshold = 0.0 if self._audit_mode.isChecked() else threshold
        self._viewer.show_pixmap(render_analysis(analysis, visible, annotated, render_threshold, self._selected_detection_index)); indexed = [(i, d) for i, d in enumerate(analysis.detections) if (self._audit_mode.isChecked() or d.confidence >= threshold) and (visible is None or d.class_name in visible)]; self._detections.setRowCount(len(indexed))
        self._detections.setProperty("detection_indices", [i for i, _ in indexed])
        for row, (_, d) in enumerate(indexed):
            values = (d.raw_class or d.class_name, d.class_name.replace("_", " ").title(), f"{d.confidence:.1%}", f"{d.bbox.x:.0f}, {d.bbox.y:.0f}, {d.bbox.width:.0f}, {d.bbox.height:.0f}", "aceptada" if d.confidence >= threshold else "descartada por umbral", d.human_review, d.corrected_class)
            for col, value in enumerate(values): self._detections.setItem(row, col, QTableWidgetItem(value))
        accepted = analysis.accepted_detections(threshold); avg = sum(d.confidence for d in accepted)/len(accepted) if accepted else 0
        counts: dict[str, int] = {}
        for detection in accepted: counts[detection.class_name] = counts.get(detection.class_name, 0) + 1
        count_text = ", ".join(f"{name.replace('_', ' ')}: {total}" for name, total in sorted(counts.items())) or "sin detecciones"
        quality = analysis.quality; quality_text = "Sin evaluación"
        if quality: quality_text = f"{quality.status} · {quality.width}×{quality.height} · brillo {quality.brightness:.0f} · contraste {quality.contrast:.0f} · nitidez {quality.sharpness:.0f}"
        warnings = list(analysis.warnings) + (list(quality.warnings) if quality else [])
        time_text = "tiempo simulado" if self._result and self._result.is_simulated else f"{analysis.inference_ms or 0:.1f} ms"
        self._field_details.setText(f"{analysis.image_path.name} · Estado: correcto · {len(accepted)} aceptadas · {len(analysis.hidden_detections(threshold))} ocultas · confianza {avg:.1%} · {time_text}\nConteos: {count_text}\nCalidad: {quality_text}" + ("\nAdvertencias: " + "; ".join(warnings) if warnings else ""))

    def _detection_selected(self, row: int, _column: int) -> None:
        indices = self._detections.property("detection_indices") or []
        if row < len(indices):
            self._selected_detection_index = indices[row]; self._refresh_view(); self._detections.selectRow(row)
            if self._result and 0 <= self._files.currentRow() < len(self._result.images):
                box = self._result.images[self._files.currentRow()].detections[self._selected_detection_index].bbox
                self._viewer.centerOn(box.x, box.y)

    def _apply_review(self) -> None:
        if not self._result or self._selected_detection_index is None: return
        image = self._result.images[self._files.currentRow()]; status = self._review_status.currentText()
        if status == "elemento_omitido":
            image.omitted_elements.append({"status": status, "class": self._corrected_class.currentText().strip()})
        else:
            detection = image.detections[self._selected_detection_index]; detection.human_review = status
            detection.corrected_class = self._corrected_class.currentText().strip() if status == "clase_equivocada" else ""
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
