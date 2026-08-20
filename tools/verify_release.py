from __future__ import annotations

import argparse
from pathlib import Path

REQUIRED_DOCS = (
    "README.md", "LICENSE", "COPYRIGHT", "SECURITY.md", "THIRD_PARTY_NOTICES.md", ".env.example",
    "docs/PROJECT_STATUS.md", "docs/DECISIONS.md",
    "docs/MODEL_CARD.md", "docs/CLASS_ONTOLOGY.md", "docs/ERROR_ANALYSIS.md", "docs/MODEL_COMPARISON.md",
)
FORBIDDEN_ROOTS = (".env", "artifacts", "build", "data_processed", "dist", "legacy", "models", "output", "runs", "tmp")
FORBIDDEN_SUFFIXES = {".pt", ".pth", ".onnx", ".engine", ".zip"}
MAX_FILE_BYTES = 5 * 1024 * 1024


def verify(root: Path) -> list[str]:
    errors = []
    for relative in REQUIRED_DOCS:
        path = root / relative
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"Falta documento requerido: {relative}")
    for relative in FORBIDDEN_ROOTS:
        if (root / relative).exists():
            errors.append(f"Contenido local no publicable presente: {relative}")
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        relative = path.relative_to(root).as_posix()
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"Binario/modelo no publicable: {relative}")
        if path.stat().st_size > MAX_FILE_BYTES:
            errors.append(f"Archivo mayor a 5 MiB: {relative}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifica que el árbol público sea pequeño y no contenga material local.")
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    errors = verify(args.root.resolve())
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print("Árbol público verificable: documentación presente y material local excluido.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
