from pathlib import Path
import tempfile

from PySide6.QtCore import QSize, Qt, QThread
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon, QPixmap
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QLineEdit,
    QFrame, QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QProgressBar, QPushButton, QSplitter, QStatusBar,
    QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget)

from src.domain.models import ImageAnalysis, StudyResult, generate_patient_id
from src.interpretation.rule_engine import interpret_study
from src.reports.pdf_report import generate_pdf
from src.services.analysis_service import AnalysisService
from src.services.export_service import export_csv, export_json
from src.processing.preprocessing import preprocess_experimental
from src.ui.analysis_worker import AnalysisWorker
from src.ui.image_renderer import fit_pixmap, legend_html, render_analysis


STYLE = """
QMainWindow, QWidget { background:#08151d; color:#dce8ee; font-family:'Segoe UI'; font-size:13px; }
QFrame#header { background:#0d202b; border-bottom:1px solid #1e3b48; }
QLabel#brand { font-size:23px; font-weight:700; color:#f4fbff; }
QLabel#subtitle, QLabel#muted { color:#83a3b2; }
QFrame.card { background:#102631; border:1px solid #20404d; border-radius:9px; }
QPushButton { background:#173844; border:1px solid #285565; border-radius:6px; padding:8px 13px; }
QPushButton:hover { background:#1d4856; } QPushButton#primary { background:#28b8a8; color:#051512; font-weight:700; }
QPushButton:disabled { color:#52717d; background:#122630; }
QListWidget, QTableWidget, QTextEdit, QComboBox { background:#0b1d26; border:1px solid #20404d; border-radius:6px; selection-background-color:#176c70; }
QHeaderView::section { background:#16333e; color:#bcd0d8; padding:7px; border:0; }
QProgressBar { border:1px solid #285565; border-radius:5px; text-align:center; background:#0b1d26; }
QProgressBar::chunk { background:#28b8a8; border-radius:4px; }
QStatusBar { background:#071118; color:#8ca8b5; }
"""


class ImageView(QGraphicsView):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(360, 280)
        self.setStyleSheet("background:#061119;border:1px solid #20404d;border-radius:8px;color:#6f909d;")
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
        self.setMinimumSize(1050, 700)
        self.setAcceptDrops(True)
        self.setStyleSheet(STYLE)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget(); layout = QVBoxLayout(root); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)
        header = QFrame(objectName="header"); h = QHBoxLayout(header); h.setContentsMargins(24, 14, 24, 14)
        titles = QVBoxLayout(); brand = QLabel("VECTOR UroSight", objectName="brand"); titles.addWidget(brand)
        titles.addWidget(QLabel("Plataforma de apoyo al análisis de sedimento urinario", objectName="subtitle")); h.addLayout(titles); h.addStretch()
        self._provider_badge = QLabel(self._provider_text()); self._provider_badge.setStyleSheet("color:#ffd66b;background:#332c16;padding:7px 12px;border-radius:6px;font-weight:700;" if self._service.is_simulated else "color:#72dfcf;background:#12352f;padding:7px 12px;border-radius:6px;font-weight:700;"); h.addWidget(self._provider_badge)
        self._folio = QLabel("NUEVO ESTUDIO", objectName="muted"); h.addWidget(self._folio); layout.addWidget(header)

        toolbar = QHBoxLayout(); toolbar.setContentsMargins(18, 12, 18, 12)
        toolbar.addWidget(QLabel("Paciente:")); self._patient_name = QLineEdit(); self._patient_name.setPlaceholderText("Nombre completo (opcional)"); self._patient_name.setMaximumWidth(240); toolbar.addWidget(self._patient_name)
        self._patient_id = QLabel(self._patient_id_value, objectName="muted"); self._patient_id.setToolTip("Identificador aleatorio generado; no contiene datos del paciente."); toolbar.addWidget(self._patient_id)
        for text, slot in (("Cargar imágenes", self._select_images), ("Cargar carpeta", self._select_folder)):
            button = QPushButton(text); button.clicked.connect(slot); toolbar.addWidget(button)
        self._analyze_button = QPushButton("Analizar estudio", objectName="primary"); self._analyze_button.clicked.connect(self._analyze); toolbar.addWidget(self._analyze_button)
        self._cancel_button = QPushButton("Cancelar"); self._cancel_button.clicked.connect(self._cancel); self._cancel_button.hide(); toolbar.addWidget(self._cancel_button)
        self._experimental_preprocess = QCheckBox("Preprocesamiento experimental"); self._experimental_preprocess.setToolTip("CLAHE + ajuste moderado + reducción ligera de ruido. Nunca modifica los originales."); toolbar.addWidget(self._experimental_preprocess)
        toolbar.addStretch(); self._export_button = QPushButton("Exportar"); self._export_button.clicked.connect(self._export); self._export_button.setEnabled(False); toolbar.addWidget(self._export_button)
        layout.addLayout(toolbar)

        splitter = QSplitter(); splitter.setChildrenCollapsible(False)
        sidebar = QFrame(); side = QVBoxLayout(sidebar); side.addWidget(QLabel("CAMPOS DEL ESTUDIO", objectName="muted"))
        self._files = QListWidget(); self._files.setIconSize(QSize(74, 54)); self._files.currentRowChanged.connect(self._select_analysis); side.addWidget(self._files)
        self._file_hint = QLabel("También puede arrastrar imágenes aquí", objectName="muted"); self._file_hint.setWordWrap(True); side.addWidget(self._file_hint); splitter.addWidget(sidebar)

        center = QFrame(); center_layout = QVBoxLayout(center)
        viewer_tools = QHBoxLayout(); self._view_mode = QComboBox(); self._view_mode.addItems(["Imagen anotada", "Imagen original"]); self._view_mode.currentIndexChanged.connect(self._refresh_view); viewer_tools.addWidget(self._view_mode)
        self._annotations = QCheckBox("Mostrar anotaciones"); self._annotations.setChecked(True); self._annotations.toggled.connect(self._refresh_view); viewer_tools.addWidget(self._annotations)
        self._audit_mode = QCheckBox("Modo de auditoría"); self._audit_mode.toggled.connect(self._audit_toggled); viewer_tools.addWidget(self._audit_mode)
        viewer_tools.addWidget(QLabel("Umbral:")); self._threshold = QDoubleSpinBox(); self._threshold.setRange(0, 1); self._threshold.setSingleStep(.05); self._threshold.setDecimals(2); self._threshold.setValue(self._service.confidence_threshold); self._threshold.valueChanged.connect(self._threshold_changed); viewer_tools.addWidget(self._threshold)
        viewer_tools.addStretch(); viewer_tools.addWidget(QLabel("Filtrar:")); self._class_filter = QComboBox(); self._class_filter.addItem("Todas las clases"); self._class_filter.currentIndexChanged.connect(self._refresh_view); viewer_tools.addWidget(self._class_filter); center_layout.addLayout(viewer_tools)
        zoom_tools = QHBoxLayout(); self._legend = QLabel("Leyenda: sin clases visibles", objectName="muted"); self._legend.setStyleSheet("color:#9eb9c4;"); zoom_tools.addWidget(self._legend); zoom_tools.addStretch()
        for text, factor in (("−", .8), ("+", 1.25)):
            button = QPushButton(text); button.setFixedWidth(38); button.clicked.connect(lambda _=False, value=factor: self._viewer.zoom(value)); zoom_tools.addWidget(button)
        reset = QPushButton("Restaurar vista"); reset.clicked.connect(self._reset_view); zoom_tools.addWidget(reset); center_layout.addLayout(zoom_tools)
        self._viewer = ImageView(); center_layout.addWidget(self._viewer, 1)
        self._field_details = QLabel("Seleccione un campo para consultar sus resultados.", objectName="muted"); self._field_details.setWordWrap(True); center_layout.addWidget(self._field_details)
        self._detections = QTableWidget(0, 7); self._detections.setHorizontalHeaderLabels(["Clase original", "Clase normalizada", "Confianza", "Caja", "Estado", "Revisión", "Corrección"]); self._detections.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self._detections.setEditTriggers(QAbstractItemView.NoEditTriggers); center_layout.addWidget(self._detections, 1)
        review_tools = QHBoxLayout(); review_tools.addWidget(QLabel("Revisión humana:")); self._review_status = QComboBox(); self._review_status.addItems(["correcta", "incorrecta", "clase_equivocada", "elemento_omitido"]); review_tools.addWidget(self._review_status); self._corrected_class = QComboBox(); self._corrected_class.setEditable(True); review_tools.addWidget(self._corrected_class); apply_review = QPushButton("Guardar revisión"); apply_review.clicked.connect(self._apply_review); review_tools.addWidget(apply_review); center_layout.addLayout(review_tools); splitter.addWidget(center)
        self._detections.cellClicked.connect(self._detection_selected)

        results = QFrame(); results_layout = QVBoxLayout(results); results_layout.addWidget(QLabel("RESUMEN DEL ESTUDIO", objectName="muted"))
        cards = QGridLayout(); self._count_card = self._card(cards, "Detecciones", 0, 0); self._confidence_card = self._card(cards, "Confianza promedio", 0, 1); self._time_card = self._card(cards, "Tiempo total", 1, 0); self._images_card = self._card(cards, "Campos procesados", 1, 1); results_layout.addLayout(cards)
        self._summary = QTableWidget(0, 3); self._summary.setHorizontalHeaderLabels(["Clase", "Total", "Promedio/campo"]); self._summary.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self._summary.setEditTriggers(QAbstractItemView.NoEditTriggers); results_layout.addWidget(self._summary)
        results_layout.addWidget(QLabel("INTERPRETACIÓN ORIENTATIVA", objectName="muted")); self._interpretation = QTextEdit(); self._interpretation.setReadOnly(True); self._interpretation.setPlaceholderText("Los hallazgos aparecerán después del análisis."); results_layout.addWidget(self._interpretation)
        warning = QLabel("PROTOTIPO ACADÉMICO · No sustituye el criterio profesional."); warning.setWordWrap(True); warning.setStyleSheet("color:#f0c96a;padding:8px;background:#2b2919;border-radius:6px;"); results_layout.addWidget(warning); splitter.addWidget(results)
        splitter.setSizes([235, 780, 390]); layout.addWidget(splitter, 1)
        self._progress = QProgressBar(); self._progress.hide(); layout.addWidget(self._progress)
        self.setStatusBar(QStatusBar()); self.statusBar().showMessage("Seleccione imágenes para comenzar.")
        self.setCentralWidget(root)
        self._audit_toggled(False)

    def _provider_text(self) -> str:
        return ("MODO DEMOSTRACIÓN - RESULTADOS SIMULADOS" if self._service.is_simulated
                else f"MOTOR ACTIVO - {self._service.provider_name.upper()}")

    @staticmethod
    def _card(layout: QGridLayout, title: str, row: int, col: int) -> QLabel:
        frame = QFrame(); frame.setProperty("class", "card"); box = QVBoxLayout(frame); box.addWidget(QLabel(title, objectName="muted")); value = QLabel("—"); value.setStyleSheet("font-size:20px;font-weight:700;color:#f4fbff;"); box.addWidget(value); layout.addWidget(frame, row, col); return value

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

    def _export(self) -> None:
        if not self._result: return
        filename, selected = QFileDialog.getSaveFileName(self, "Exportar resultados", f"VECTOR_UroSight_{self._result.study_id}.pdf", "PDF (*.pdf);;JSON (*.json);;CSV (*.csv)")
        if not filename: return
        path = Path(filename)
        try:
            if "JSON" in selected: path = path.with_suffix(".json"); export_json(self._result, path)
            elif "CSV" in selected: path = path.with_suffix(".csv"); export_csv(self._result, path)
            else: path = path.with_suffix(".pdf"); generate_pdf(self._result, path)
            self.statusBar().showMessage(f"Archivo exportado: {path}")
        except Exception as exc: QMessageBox.critical(self, "No se pudo exportar", str(exc))

    def closeEvent(self, event) -> None:
        if self._thread and self._thread.isRunning():
            if self._worker: self._worker.cancel()
            self._close_when_finished = True
            self.statusBar().showMessage("Finalizando el campo en curso antes de cerrar…")
            event.ignore()
            return
        if self._preprocess_temp: self._preprocess_temp.cleanup()
        event.accept()
