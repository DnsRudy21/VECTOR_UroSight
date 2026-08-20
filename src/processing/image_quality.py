from pathlib import Path

from PIL import Image, ImageFilter, ImageStat

from src.domain.models import ImageQuality

# Indicadores técnicos heurísticos, no criterios clínicos. Escala de grises 0-255.
LOW_BRIGHTNESS = 45.0
HIGH_BRIGHTNESS = 215.0
LOW_CONTRAST = 20.0
LOW_EDGE_VARIANCE = 35.0


def assess_image_quality(path: Path) -> ImageQuality:
    with Image.open(path) as source:
        gray = source.convert("L")
        gray.thumbnail((1024, 1024))
        stats = ImageStat.Stat(gray)
        brightness = float(stats.mean[0])
        contrast = float(stats.stddev[0])
        edges = gray.filter(ImageFilter.FIND_EDGES)
        if edges.width > 4 and edges.height > 4:
            edges = edges.crop((2, 2, edges.width - 2, edges.height - 2))
        sharpness = float(ImageStat.Stat(edges).var[0])
        warnings: list[str] = []
        if brightness < LOW_BRIGHTNESS:
            warnings.append("Brillo muy bajo")
        elif brightness > HIGH_BRIGHTNESS:
            warnings.append("Brillo excesivo")
        if contrast < LOW_CONTRAST:
            warnings.append("Contraste insuficiente")
        if sharpness < LOW_EDGE_VARIANCE:
            warnings.append("Posible desenfoque")
        return ImageQuality(source.width, source.height, brightness, contrast, sharpness, tuple(warnings))
