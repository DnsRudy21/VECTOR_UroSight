DISCLAIMER = (
    "Interpretación orientativa para fines académicos. Los resultados requieren revisión "
    "por el profesional del laboratorio, deben correlacionarse con el resto del examen y no constituyen un diagnóstico."
)


def interpret(counts: dict[str, int], image_count: int) -> list[str]:
    messages: list[str] = []
    divisor = max(image_count, 1)
    rbc_avg = counts.get("eritrocitos", 0) / divisor
    wbc_avg = counts.get("leucocitos", 0) / divisor
    if not counts:
        messages.append("No se registraron detecciones con el umbral configurado.")
    if rbc_avg > 5:
        messages.append("Se observa una presencia elevada de detecciones compatibles con eritrocitos en las imágenes analizadas.")
    elif counts.get("eritrocitos", 0):
        messages.append("Se identificaron detecciones compatibles con eritrocitos.")
    if wbc_avg > 5:
        messages.append("Se observa una presencia elevada de detecciones compatibles con leucocitos en las imágenes analizadas.")
    elif counts.get("leucocitos", 0):
        messages.append("Se identificaron detecciones compatibles con leucocitos.")
    if counts.get("celulas_epiteliales", 0):
        messages.append("Se identificaron detecciones compatibles con células epiteliales.")
    if counts.get("celulas_epiteliales_nucleadas", 0):
        messages.append("Se identificaron estructuras clasificadas como núcleos epiteliales; requieren confirmación visual.")
    if counts.get("cristales", 0):
        messages.append("Se detectaron estructuras clasificadas como cristales; se recomienda confirmación manual.")
    if counts.get("cilindros", 0):
        messages.append("Se detectaron estructuras clasificadas como cilindros; se recomienda revisión profesional.")
    if counts.get("levaduras_hongos", 0):
        messages.append("Se detectaron estructuras clasificadas como hongos o levaduras; se recomienda confirmación profesional.")
    messages.append(DISCLAIMER)
    return messages


def interpret_study(result) -> list[str]:
    messages = interpret(result.class_counts(), len(result.successful_images))
    counts = result.class_counts()
    if counts:
        predominant = max(counts, key=counts.get)
        fields = result.fields_by_class().get(predominant, 0)
        messages.insert(0, f"La clase predominante fue {predominant.replace('_', ' ')}, presente en {fields} de {len(result.successful_images)} campos procesados.")
    if result.hidden_count():
        messages.insert(-1, f"{result.hidden_count()} detección(es) quedaron ocultas por el umbral de confianza y se conservan para trazabilidad.")
    quality_fields = sum(bool(image.quality and image.quality.warnings) for image in result.successful_images)
    if quality_fields:
        messages.insert(-1, f"{quality_fields} campo(s) presentan indicadores técnicos de calidad que ameritan revisión visual.")
    return messages
