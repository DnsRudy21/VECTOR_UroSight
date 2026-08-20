"""Genera un informe reproducible de demostración con el modelo local congelado."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.inference.local_yolo_provider import LocalYoloProvider
from src.reports.pdf_report import generate_pdf
from src.services.analysis_service import AnalysisService


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--confidence", type=float, default=0.25)
    args = parser.parse_args()

    paths = AnalysisService.collect_folder(args.images)[:6]
    provider = LocalYoloProvider(args.model, confidence=args.confidence)
    result = AnalysisService(provider).analyze(paths, source="Auditoría final reproducible: 6 imágenes")
    result.patient_name = "Paciente de demostración"
    result.patient_id = "PT-DEMO-000001"
    generate_pdf(result, args.output)
    print(f"PDF generado: {args.output}")
    print(f"Imágenes: {len(result.successful_images)}; detecciones: {sum(result.class_counts().values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
