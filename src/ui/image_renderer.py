from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen, QPixmap

from src.domain.models import ImageAnalysis


CLASS_COLORS = {
    "eritrocitos": QColor("#ef6461"),
    "leucocitos": QColor("#39c6b4"),
    "celulas_epiteliales": QColor("#f5b942"),
    "celulas_epiteliales_nucleadas": QColor("#c58af9"),
    "cristales": QColor("#5aa9ff"),
    "cilindros": QColor("#ff8a5b"),
    "levaduras_hongos": QColor("#d7ef6b"),
}


def legend_html(classes: set[str]) -> str:
    parts = []
    for name in sorted(classes):
        color = CLASS_COLORS.get(name, QColor("#6ea8fe")).name()
        parts.append(f'<font color="{color}">■</font> {name.replace("_", " ")}')
    return "Leyenda: " + " &nbsp; ".join(parts) if parts else "Leyenda: sin clases visibles"


def render_analysis(analysis: ImageAnalysis, visible_classes: set[str] | None = None,
                    annotations: bool = True, threshold: float = 0.0,
                    selected_index: int | None = None) -> QPixmap:
    image = QImage(str(analysis.image_path))
    if image.isNull():
        return QPixmap()
    pixmap = QPixmap.fromImage(image)
    if not annotations:
        return pixmap
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
    for index, detection in enumerate(analysis.detections):
        if detection.confidence < threshold:
            continue
        if visible_classes is not None and detection.class_name not in visible_classes:
            continue
        color = CLASS_COLORS.get(detection.class_name, QColor("#6ea8fe"))
        selected = selected_index == index
        painter.setOpacity(1.0 if selected_index is None or selected else 0.3)
        painter.setPen(QPen(QColor("#ffffff") if selected else color, 5 if selected else 3))
        box = detection.bbox
        x, y = box.x - box.width / 2, box.y - box.height / 2
        painter.drawRect(int(x), int(y), int(box.width), int(box.height))
        label = f"{detection.class_name.replace('_', ' ')}  {detection.confidence:.0%}"
        metrics = painter.fontMetrics()
        width = metrics.horizontalAdvance(label) + 12
        top = max(0, int(y) - 24)
        painter.fillRect(int(x), top, width, 22, color)
        painter.setPen(QColor("#07151d"))
        painter.drawText(int(x) + 6, top + 16, label)
    painter.end()
    return pixmap


def fit_pixmap(pixmap: QPixmap, width: int, height: int) -> QPixmap:
    return pixmap.scaled(max(width, 1), max(height, 1), Qt.KeepAspectRatio, Qt.SmoothTransformation)
