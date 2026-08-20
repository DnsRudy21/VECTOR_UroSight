from pathlib import Path

from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
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


def _annotated_preview(result: StudyResult, analysis: ImageAnalysis, output_path: Path) -> Path:
    with PILImage.open(analysis.image_path) as source:
        preview = source.convert("RGB"); draw = ImageDraw.Draw(preview)
        font = ImageFont.load_default(size=max(14, preview.width // 55))
        line_width = max(3, preview.width // 250)
        for detection in result.detections_for(analysis):
            box = detection.bbox; bounds = (box.x-box.width/2, box.y-box.height/2, box.x+box.width/2, box.y+box.height/2)
            color = CLASS_HEX.get(detection.class_name, "#377DCE")
            draw.rectangle(bounds, outline=color, width=line_width)
            label = f"{detection.class_name.replace('_', ' ')} {detection.confidence:.0%}"
            left, top, right, bottom = draw.textbbox((0,0), label, font=font)
            label_y = max(0, int(bounds[1])-(bottom-top)-8)
            draw.rectangle((bounds[0], label_y, bounds[0]+right-left+10, label_y+bottom-top+6), fill=color)
            draw.text((bounds[0]+5, label_y+2), label, font=font, fill="white")
        preview.thumbnail((1500, 1050)); preview.save(output_path, "PNG")
    return output_path


def generate_pdf(result: StudyResult, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output_path), pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm,
                            topMargin=1.35*cm, bottomMargin=1.5*cm, title=f"VECTOR UroSight - {result.study_id}")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("Brand", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, textColor=NAVY, spaceAfter=2))
    styles.add(ParagraphStyle("Sub", parent=styles["Normal"], fontSize=10, textColor=MUTED, spaceAfter=12))
    styles.add(ParagraphStyle("Notice", parent=styles["BodyText"], backColor=colors.HexColor("#FFF3C9"), borderColor=AMBER, borderWidth=.6, borderPadding=8, leading=13, spaceAfter=8))
    styles.add(ParagraphStyle("Demo", parent=styles["BodyText"], backColor=colors.HexColor("#FFE5A8"), borderColor=AMBER, borderWidth=1, borderPadding=9, textColor=colors.HexColor("#5A3D00"), fontName="Helvetica-Bold", alignment=1, spaceAfter=10))
    story = [Paragraph("VECTOR UroSight", styles["Brand"]), Paragraph("Plataforma de apoyo al análisis de imágenes de sedimento urinario", styles["Sub"])]
    if result.is_simulated: story.append(Paragraph("MODO DEMOSTRACIÓN - RESULTADOS SIMULADOS", styles["Demo"]))
    patient_name = result.patient_name or "No capturado"
    meta = [[Paragraph("ID de paciente", styles["BodyText"]), Paragraph(result.patient_id, styles["BodyText"]),
             Paragraph("Paciente", styles["BodyText"]), Paragraph(patient_name, styles["BodyText"])],
            [Paragraph("Folio interno", styles["BodyText"]), Paragraph(result.study_id, styles["BodyText"]),
             Paragraph("Fecha y hora", styles["BodyText"]), Paragraph(result.created_at.strftime("%Y-%m-%d %H:%M"), styles["BodyText"])],
            [Paragraph("Proveedor activo", styles["BodyText"]), Paragraph(result.provider_name, styles["BodyText"]),
             Paragraph("Umbral", styles["BodyText"]), Paragraph(f"{result.confidence_threshold:.0%}", styles["BodyText"])],
            [Paragraph("Campos procesados", styles["BodyText"]), Paragraph(str(len(result.successful_images)), styles["BodyText"]),
             Paragraph("Campos con error", styles["BodyText"]), Paragraph(str(len(result.failed_images)), styles["BodyText"])],
            [Paragraph("Origen", styles["BodyText"]), Paragraph(result.source or "No especificado", styles["BodyText"]),
             Paragraph("Tiempo de inferencia", styles["BodyText"]), Paragraph("No aplica - tiempo simulado" if result.is_simulated else f"{result.total_inference_ms():.1f} ms", styles["BodyText"])]]
    info = _table(meta, [3.4*cm, 5.2*cm, 3.7*cm, 4.7*cm]); info.setStyle(TableStyle([("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"), ("FONTNAME", (2,0), (2,-1), "Helvetica-Bold"), ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#E8F0F2")), ("BACKGROUND", (2,0), (2,-1), colors.HexColor("#E8F0F2"))]))
    story += [info, Spacer(1, 12), Paragraph("Resumen consolidado", styles["Heading2"])]
    counts, averages = result.class_counts(), result.averages_per_image()
    rows = [["Clase", "Total", "Promedio por campo", "Confianza media", "Presencia"]]
    for name, total in sorted(counts.items()):
        values = [d.confidence for image in result.successful_images for d in result.detections_for(image) if d.class_name == name]
        rows.append([name.replace("_", " ").title(), str(total), f"{averages[name]:.2f}", f"{sum(values)/len(values):.1%}", f"{result.fields_by_class()[name]}/{len(result.successful_images)}"])
    if len(rows) == 1: rows.append(["Sin detecciones", "0", "0.00", "-", "0"])
    story += [_table(rows, [4.8*cm, 2*cm, 3.8*cm, 3.2*cm, 3.2*cm], True), Spacer(1, 9),
              Paragraph(f"Confianza promedio global: <b>{result.average_confidence():.1%}</b> &nbsp;&nbsp; Detecciones ocultas por umbral: <b>{result.hidden_count()}</b> &nbsp;&nbsp; Requieren revisión: <b>{result.review_count()}</b>", styles["BodyText"]),
              Spacer(1, 6)]
    reviews = result.human_review_summary()
    original_total = sum(len(image.raw_detections) for image in result.successful_images)
    accepted_review = sum(len(result.reviewed_detections_for(image)) for image in result.successful_images)
    story += [Paragraph(f"Auditoría: predicciones originales <b>{original_total}</b> · aceptadas tras revisión <b>{accepted_review}</b> · rechazadas <b>{reviews.get('incorrecta', 0)}</b> · correcciones humanas <b>{reviews.get('clase_equivocada', 0)}</b> · elementos omitidos <b>{reviews.get('elemento_omitido', 0)}</b>", styles["BodyText"]),
              Spacer(1, 10), Paragraph("Interpretación orientativa", styles["Heading2"])]
    for message in interpret_study(result): story += [Paragraph(message, styles["BodyText"]), Spacer(1, 4)]
    story += [Spacer(1, 6), Paragraph("Limitación: los conteos representan detecciones por imagen cargada. No equivalen automáticamente a valores clínicos por campo microscópico sin controlar aumento, preparación, área y protocolo. Los indicadores de calidad son heurísticas técnicas, no una evaluación clínica.", styles["Notice"])]

    evidence_limit = 6 if result.audit_mode else 4
    selected = sorted(result.successful_images, key=lambda image: len(result.detections_for(image)), reverse=True)[:evidence_limit]
    if selected:
        criterion = ("Modo auditoría: se incluyen hasta seis campos con mayor número de detecciones aceptadas."
                     if result.audit_mode else "Criterio de selección: hasta cuatro campos con mayor número de detecciones aceptadas al umbral configurado.")
        story += [PageBreak(), Paragraph("Evidencia visual", styles["Heading2"]), Paragraph(criterion, styles["Sub"])]
    temp_paths: list[Path] = []
    for index, analysis in enumerate(selected, 1):
        if index > 1:
            story.append(PageBreak())
        accepted = result.detections_for(analysis); average = sum(d.confidence for d in accepted)/len(accepted) if accepted else 0
        quality = analysis.quality; quality_status = quality.status if quality else "No evaluada"
        field_story = [Paragraph(f"Campo {index}: {analysis.image_path.name}", styles["Heading2"]),
                       _table([["Detecciones", str(len(accepted)), "Confianza promedio", f"{average:.1%}"],
                               ["Originales", str(len(analysis.raw_detections)), "Estado de calidad", quality_status],
                               ["Ocultas/rechazadas", str(len(analysis.hidden_detections(result.confidence_threshold)) + sum(d.human_review == 'incorrecta' for d in analysis.detections)), "Variante", analysis.processing_variant]], [3.7*cm, 3.0*cm, 4.4*cm, 5.9*cm]),
                       Spacer(1, 7), Paragraph(f"Conteos: {_field_counts(result, analysis)}", styles["BodyText"])]
        quality_warnings = ", ".join(quality.warnings) if quality and quality.warnings else "Sin alertas técnicas"
        field_story += [Paragraph(f"Calidad: {quality_warnings}", styles["BodyText"]), Spacer(1, 7)]
        raw_names = sorted({d.raw_class or d.class_name for d in analysis.detections})
        normalized_names = sorted({d.class_name for d in analysis.detections})
        field_story += [Paragraph(f"Clases crudas: {', '.join(raw_names) or 'ninguna'} · Normalizadas: {', '.join(normalized_names) or 'ninguna'}", styles["BodyText"]), Spacer(1, 5)]
        temp_path = output_path.parent / f".{output_path.stem}_preview_{index}.png"; temp_paths.append(temp_path)
        try:
            _annotated_preview(result, analysis, temp_path)
            field_story += [Image(str(temp_path), width=15.5*cm, height=9.2*cm, kind="proportional"), Spacer(1, 7)]
        except OSError:
            field_story += [Paragraph("No fue posible incluir la vista previa de este campo.", styles["Notice"])]
        present_classes = {d.effective_class for d in result.detections_for(analysis)}
        legend = " &nbsp;&nbsp; ".join(f'<font color="{CLASS_HEX.get(name, "#377DCE")}">■</font> {name.replace("_", " ")}' for name in sorted(present_classes)) or "Sin clases aceptadas"
        field_story += [Paragraph(f"Leyenda: {legend}", styles["BodyText"])]
        story.extend(field_story)
        story.append(Spacer(1, 6))
    if selected:
        story.append(Paragraph("Fin de la evidencia seleccionada.", styles["Sub"]))
    try:
        doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    finally:
        for path in temp_paths:
            try: path.unlink()
            except OSError: pass
    return output_path
