from pathlib import Path

from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.domain.models import ImageAnalysis, StudyResult
from src.interpretation.rule_engine import interpret_study

NAVY = colors.HexColor("#102631")
TEAL = colors.HexColor("#169E91")
MUTED = colors.HexColor("#58717D")
AMBER = colors.HexColor("#E3A928")
CLASS_HEX = {"eritrocitos": "#E34F4F", "leucocitos": "#159E91", "celulas_epiteliales": "#D89B1D",
             "celulas_epiteliales_nucleadas": "#A45DE0", "cristales": "#377DCE",
             "cilindros": "#F07842", "levaduras_hongos": "#7E9C18"}


def _footer(canvas, doc) -> None:
    canvas.saveState(); canvas.setStrokeColor(colors.HexColor("#D8E2E6"))
    canvas.line(1.5*cm, 1.15*cm, A4[0]-1.5*cm, 1.15*cm)
    canvas.setFont("Helvetica", 8); canvas.setFillColor(MUTED)
    canvas.drawString(1.5*cm, .75*cm, "VECTOR UroSight - Prototipo académico")
    canvas.drawRightString(A4[0]-1.5*cm, .75*cm, f"Página {doc.page}"); canvas.restoreState()


def _page_header(styles) -> Table:
    data = [[Paragraph("<font color='#FFFFFF'><b>VECTOR UroSight</b></font>", styles["BodyText"]),
             Paragraph("<font color='#FFFFFF'>REPORTE DE ANÁLISIS ASISTIDO</font>", styles["BodyText"])]]
    header = Table(data, colWidths=[10.5*cm, 6.5*cm])
    header.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),NAVY),("ALIGN",(1,0),(1,0),"RIGHT"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),12),("RIGHTPADDING",(0,0),(-1,-1),12),("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10)]))
    return header


def _table(data, widths, header=False) -> Table:
    table = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    style = [("GRID", (0,0), (-1,-1), .35, colors.HexColor("#B8CBD2")),
             ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("LEFTPADDING", (0,0), (-1,-1), 8),
             ("RIGHTPADDING", (0,0), (-1,-1), 8), ("TOPPADDING", (0,0), (-1,-1), 7),
             ("BOTTOMPADDING", (0,0), (-1,-1), 7),
             ("ROWBACKGROUNDS", (0,1 if header else 0), (-1,-1), [colors.white, colors.HexColor("#F1F6F7")])]
    if header:
        style += [("BACKGROUND", (0,0), (-1,0), NAVY), ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                  ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"), ("FONTSIZE", (0,0), (-1,0), 8.5)]
    table.setStyle(TableStyle(style)); return table


def _field_counts(result: StudyResult, analysis: ImageAnalysis) -> str:
    counts: dict[str, int] = {}
    for detection in result.detections_for(analysis): counts[detection.class_name] = counts.get(detection.class_name, 0) + 1
    return ", ".join(f"{name.replace('_', ' ')}: {total}" for name, total in sorted(counts.items())) or "Sin detecciones aceptadas"


def annotated_image(result: StudyResult, analysis: ImageAnalysis, output_path: Path, *, preview: bool = False) -> Path:
    with PILImage.open(analysis.image_path) as source:
        rendered = source.convert("RGB"); draw = ImageDraw.Draw(rendered)
        font = ImageFont.load_default(size=max(14, rendered.width // 55))
        line_width = max(3, rendered.width // 250)
        for detection in result.detections_for(analysis):
            box = detection.bbox; bounds = (box.x-box.width/2, box.y-box.height/2, box.x+box.width/2, box.y+box.height/2)
            color = CLASS_HEX.get(detection.class_name, "#377DCE")
            draw.rectangle(bounds, outline=color, width=line_width)
            label = f"{detection.class_name.replace('_', ' ')} {detection.confidence:.0%}"
            left, top, right, bottom = draw.textbbox((0,0), label, font=font)
            label_y = max(0, int(bounds[1])-(bottom-top)-8)
            draw.rectangle((bounds[0], label_y, bounds[0]+right-left+10, label_y+bottom-top+6), fill=color)
            draw.text((bounds[0]+5, label_y+2), label, font=font, fill="white")
        if preview: rendered.thumbnail((1500, 1050))
        rendered.save(output_path, "PNG")
    return output_path


def export_annotated_images(result: StudyResult, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True); exported = []
    for analysis in result.successful_images:
        path = output_dir / f"{analysis.image_path.stem}_anotada.png"
        exported.append(annotated_image(result, analysis, path))
    return exported


def _distribution_chart(counts: dict[str, int], width: float = 470, height: float | None = None) -> Drawing:
    height = height or max(65, len(counts) * 19 + 12)
    drawing = Drawing(width, height); maximum = max(counts.values(), default=1); y = height - 20
    for name, total in sorted(counts.items(), key=lambda item: item[1], reverse=True):
        label = name.replace("_", " ").title()[:23]; color = colors.HexColor(CLASS_HEX.get(name, "#169E91"))
        drawing.add(String(0, y, label, fontName="Helvetica", fontSize=8, fillColor=NAVY))
        drawing.add(Rect(120, y - 2, 285 * total / maximum, 10, rx=4, ry=4, fillColor=color, strokeColor=None))
        drawing.add(String(415, y, str(total), fontName="Helvetica-Bold", fontSize=8, fillColor=NAVY)); y -= 19
    return drawing


def _gallery_layout(total: int) -> tuple[int, int, float, float]:
    """Columns, rows, preview width and preview height for an adaptive evidence page."""
    if total == 1:
        return 1, 1, 14.8*cm, 10.8*cm
    if total == 2:
        return 1, 2, 13.5*cm, 7.2*cm
    if total <= 6:
        return 2, 3, 7.8*cm, 4.8*cm
    return 3, 4, 5.15*cm, 3.55*cm


def _gallery_cell(result: StudyResult, analysis: ImageAnalysis, preview_path: Path,
                  width: float, height: float, styles) -> Table:
    accepted = result.detections_for(analysis)
    average = sum(d.confidence for d in accepted) / len(accepted) if accepted else 0
    caption = Paragraph(
        f"<b>{analysis.image_path.name}</b><br/>"
        f"{len(accepted)} hallazgos · score {average:.1%}<br/>"
        f"{_field_counts(result, analysis)}",
        ParagraphStyle("GalleryCaption", parent=styles["BodyText"], fontSize=7.2,
                       leading=9, textColor=NAVY, spaceAfter=0),
    )
    content = [[Image(str(preview_path), width=width, height=height, kind="proportional")], [caption]]
    card = Table(content, colWidths=[width + .25*cm], hAlign="CENTER")
    card.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.white),
        ("BOX", (0,0), (-1,-1), .45, colors.HexColor("#C7D7DD")),
        ("LEFTPADDING", (0,0), (-1,-1), 4), ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,0), 4), ("BOTTOMPADDING", (0,0), (-1,0), 3),
        ("TOPPADDING", (0,1), (-1,1), 4), ("BOTTOMPADDING", (0,1), (-1,1), 5),
    ]))
    return card


def generate_pdf(result: StudyResult, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output_path), pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm,
                            topMargin=1.0*cm, bottomMargin=1.5*cm, title=f"VECTOR UroSight - {result.study_id}")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("Brand", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, textColor=NAVY, spaceAfter=2))
    styles.add(ParagraphStyle("Sub", parent=styles["Normal"], fontSize=10, textColor=MUTED, spaceAfter=12))
    styles.add(ParagraphStyle("Notice", parent=styles["BodyText"], backColor=colors.HexColor("#FFF3C9"), borderColor=AMBER, borderWidth=.6, borderPadding=8, leading=13, spaceAfter=8))
    styles.add(ParagraphStyle("Demo", parent=styles["BodyText"], backColor=colors.HexColor("#FFE5A8"), borderColor=AMBER, borderWidth=1, borderPadding=9, textColor=colors.HexColor("#5A3D00"), fontName="Helvetica-Bold", alignment=1, spaceAfter=10))
    styles.add(ParagraphStyle("Section", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, textColor=NAVY, spaceBefore=8, spaceAfter=7))
    styles.add(ParagraphStyle("Kpi", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=17, textColor=NAVY, leading=20, alignment=1))
    story = [_page_header(styles), Spacer(1, 14), Paragraph("Resumen del estudio", styles["Brand"]), Paragraph(f"Folio {result.study_id} · Generado {result.created_at.strftime('%d/%m/%Y %H:%M')}", styles["Sub"])]
    if result.is_simulated: story.append(Paragraph("MODO DEMOSTRACIÓN - RESULTADOS SIMULADOS", styles["Demo"]))
    patient_name = result.patient_name or "No capturado"
    meta = [[Paragraph("ID de paciente", styles["BodyText"]), Paragraph(result.patient_id, styles["BodyText"]),
             Paragraph("Paciente", styles["BodyText"]), Paragraph(patient_name, styles["BodyText"])],
            [Paragraph("Folio interno", styles["BodyText"]), Paragraph(result.study_id, styles["BodyText"]),
             Paragraph("Fecha y hora", styles["BodyText"]), Paragraph(result.created_at.strftime("%Y-%m-%d %H:%M"), styles["BodyText"])],
            [Paragraph("Motor de análisis", styles["BodyText"]), Paragraph("Demostración simulada" if result.is_simulated else "YOLO11s", styles["BodyText"]),
             Paragraph("Umbral", styles["BodyText"]), Paragraph(f"{result.confidence_threshold:.0%}", styles["BodyText"])],
            [Paragraph("Campos procesados", styles["BodyText"]), Paragraph(str(len(result.successful_images)), styles["BodyText"]),
             Paragraph("Campos con error", styles["BodyText"]), Paragraph(str(len(result.failed_images)), styles["BodyText"])],
            [Paragraph("Origen", styles["BodyText"]), Paragraph(result.source or "No especificado", styles["BodyText"]),
             Paragraph("Tiempo de inferencia", styles["BodyText"]), Paragraph("No aplica - tiempo simulado" if result.is_simulated else f"{result.total_inference_ms():.1f} ms", styles["BodyText"])]]
    info = _table(meta, [3.4*cm, 5.2*cm, 3.7*cm, 4.7*cm]); info.setStyle(TableStyle([("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"), ("FONTNAME", (2,0), (2,-1), "Helvetica-Bold"), ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#E8F0F2")), ("BACKGROUND", (2,0), (2,-1), colors.HexColor("#E8F0F2"))]))
    story += [info, Spacer(1, 10)]
    counts, averages = result.class_counts(), result.averages_per_image()
    kpis = [[Paragraph(f"{sum(counts.values())}<br/><font size='7' color='#58717D'>DETECCIONES</font>", styles["Kpi"]),
             Paragraph(f"{result.average_confidence():.1%}<br/><font size='7' color='#58717D'>SCORE PROMEDIO</font>", styles["Kpi"]),
             Paragraph(f"{len(result.successful_images)}<br/><font size='7' color='#58717D'>CAMPOS</font>", styles["Kpi"]),
             Paragraph(f"{result.confidence_threshold:.0%}<br/><font size='7' color='#58717D'>UMBRAL</font>", styles["Kpi"])]]
    kpi_table = Table(kpis, colWidths=[4.25*cm]*4); kpi_table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#EAF4F5")),("BOX",(0,0),(-1,-1),.5,colors.HexColor("#C9DDE2")),("INNERGRID",(0,0),(-1,-1),.5,colors.HexColor("#C9DDE2")),("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10)]))
    story += [kpi_table, Spacer(1, 12), Paragraph("Distribución de hallazgos", styles["Section"]), _distribution_chart(counts), Spacer(1, 5), Paragraph("Detalle estadístico", styles["Section"])]
    rows = [["Clase", "Total", "Promedio por campo", "Score medio", "Presencia"]]
    for name, total in sorted(counts.items()):
        values = [d.confidence for image in result.successful_images for d in result.detections_for(image) if d.class_name == name]
        rows.append([name.replace("_", " ").title(), str(total), f"{averages[name]:.2f}", f"{sum(values)/len(values):.1%}", f"{result.fields_by_class()[name]}/{len(result.successful_images)}"])
    if len(rows) == 1: rows.append(["Sin detecciones", "0", "0.00", "-", "0"])
    story += [_table(rows, [4.8*cm, 2*cm, 3.8*cm, 3.2*cm, 3.2*cm], True), Spacer(1, 9),
              Paragraph(f"Score promedio del modelo: <b>{result.average_confidence():.1%}</b> &nbsp;&nbsp; Detecciones ocultas por umbral: <b>{result.hidden_count()}</b> &nbsp;&nbsp; Requieren revisión: <b>{result.review_count()}</b>", styles["BodyText"]),
              Spacer(1, 6)]
    reviews = result.human_review_summary()
    original_total = sum(len(image.raw_detections) for image in result.successful_images)
    accepted_review = sum(len(result.reviewed_detections_for(image)) for image in result.successful_images)
    story += [Paragraph(f"Auditoría: predicciones originales <b>{original_total}</b> · aceptadas tras revisión <b>{accepted_review}</b> · rechazadas <b>{reviews.get('incorrecta', 0)}</b> · correcciones humanas <b>{reviews.get('clase_equivocada', 0)}</b> · elementos omitidos <b>{reviews.get('elemento_omitido', 0)}</b>", styles["BodyText"]),
              Spacer(1, 8), PageBreak(), Paragraph("Interpretación orientativa", styles["Section"])]
    for message in interpret_study(result): story += [Paragraph(message, styles["BodyText"]), Spacer(1, 4)]
    story += [Spacer(1, 6), Paragraph("Limitación: los conteos representan detecciones por imagen cargada. No equivalen automáticamente a valores clínicos por campo microscópico sin controlar aumento, preparación, área y protocolo. Los indicadores de calidad son heurísticas técnicas, no una evaluación clínica.", styles["Notice"])]

    selected = list(result.successful_images)
    if selected:
        story += [PageBreak(), Paragraph("Evidencia visual completa", styles["Section"]),
                  Paragraph(f"Se incluyen los {len(selected)} campos procesados. La cuadrícula se adapta automáticamente al tamaño del estudio; las imágenes anotadas también pueden exportarse en resolución completa.", styles["Sub"])]
    temp_paths: list[Path] = []
    columns, rows_per_page, preview_width, preview_height = _gallery_layout(len(selected))
    cards = []
    for index, analysis in enumerate(selected, 1):
        temp_path = output_path.parent / f".{output_path.stem}_preview_{index:03d}.png"; temp_paths.append(temp_path)
        try:
            annotated_image(result, analysis, temp_path, preview=True)
            cards.append(_gallery_cell(result, analysis, temp_path, preview_width, preview_height, styles))
        except OSError:
            cards.append(Paragraph(f"{analysis.image_path.name}<br/>Vista previa no disponible", styles["Notice"]))
    page_size = columns * rows_per_page
    for page_start in range(0, len(cards), page_size):
        if page_start:
            story += [PageBreak(), Paragraph("Evidencia visual completa", styles["Section"]),
                      Paragraph(f"Campos {page_start + 1} a {min(page_start + page_size, len(cards))} de {len(cards)}", styles["Sub"])]
        page_cards = cards[page_start:page_start + page_size]
        grid = [page_cards[i:i + columns] for i in range(0, len(page_cards), columns)]
        while len(grid[-1]) < columns: grid[-1].append("")
        gallery = Table(grid, colWidths=[17*cm/columns]*columns, hAlign="CENTER")
        gallery.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"),
                                     ("LEFTPADDING", (0,0), (-1,-1), 3), ("RIGHTPADDING", (0,0), (-1,-1), 3),
                                     ("TOPPADDING", (0,0), (-1,-1), 3), ("BOTTOMPADDING", (0,0), (-1,-1), 4)]))
        story.append(gallery)
    if selected:
        story.append(Paragraph(f"Fin de la evidencia · {len(selected)} de {len(selected)} campos incluidos.", styles["Sub"]))
    try:
        doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    finally:
        for path in temp_paths:
            try: path.unlink()
            except OSError: pass
    return output_path
