from pathlib import Path


def preprocess_experimental(image_path: Path, output_path: Path) -> Path:
    """CLAHE, moderate brightness/contrast and light denoising; source is never overwritten."""
    import cv2
    source = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if source is None: raise ValueError(f"No se pudo preprocesar la imagen: {image_path.name}")
    lab = cv2.cvtColor(source, cv2.COLOR_BGR2LAB); luminance, a_channel, b_channel = cv2.split(lab)
    enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(luminance)
    merged = cv2.cvtColor(cv2.merge((enhanced, a_channel, b_channel)), cv2.COLOR_LAB2BGR)
    adjusted = cv2.convertScaleAbs(merged, alpha=1.05, beta=3)
    denoised = cv2.bilateralFilter(adjusted, d=5, sigmaColor=25, sigmaSpace=25)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output_path), denoised): raise OSError(f"No se pudo guardar: {output_path.name}")
    return output_path
