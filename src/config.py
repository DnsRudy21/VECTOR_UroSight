from dataclasses import dataclass
import os
import json
from pathlib import Path
import sys

from dotenv import load_dotenv


def application_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path.cwd()


def user_configuration_root() -> Path:
    return Path(sys.executable).parent if getattr(sys, "frozen", False) else Path.cwd()


load_dotenv(user_configuration_root() / ".env")


def _confidence_from_env() -> float:
    raw = os.getenv("CONFIDENCE_THRESHOLD", "0.44")
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError("CONFIDENCE_THRESHOLD debe ser un número entre 0 y 1.") from exc
    if not 0 <= value <= 1:
        raise ValueError("CONFIDENCE_THRESHOLD debe estar entre 0 y 1.")
    return value


def _imgsz_from_env() -> int:
    raw = os.getenv("LOCAL_MODEL_IMGSZ", "448")
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError("LOCAL_MODEL_IMGSZ debe ser un entero positivo múltiplo de 32.") from exc
    if value <= 0 or value % 32:
        raise ValueError("LOCAL_MODEL_IMGSZ debe ser un entero positivo múltiplo de 32.")
    return value


def _boolean_from_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "true" if default else "false").strip().lower()
    if raw not in {"1", "0", "true", "false", "yes", "no"}:
        raise ValueError(f"{name} debe ser true o false.")
    return raw in {"1", "true", "yes"}


def _max_detections_from_env() -> int:
    try:
        value = int(os.getenv("LOCAL_MODEL_MAX_DETECTIONS", "300"))
    except ValueError as exc:
        raise ValueError("LOCAL_MODEL_MAX_DETECTIONS debe ser un entero positivo.") from exc
    if value <= 0:
        raise ValueError("LOCAL_MODEL_MAX_DETECTIONS debe ser un entero positivo.")
    return value


@dataclass(frozen=True)
class Settings:
    inference_provider: str
    local_model_path: Path
    local_model_imgsz: int
    local_model_augment: bool
    confidence_threshold: float
    local_model_max_detections: int = 300

    @classmethod
    def from_environment(cls) -> "Settings":
        final_dir = application_root() / "models" / "vector_urosight" / "final"
        if getattr(sys, "frozen", False):
            config = json.loads((final_dir / "evaluation_config.json").read_text(encoding="utf-8"))
            return cls("local", final_dir / "best.pt", config["imgsz"], config["augment"],
                       config["operating_confidence"], config["max_det"])
        bundled_model = application_root() / "models" / "vector_urosight" / "best.pt"
        default_provider = "local" if getattr(sys, "frozen", False) and bundled_model.is_file() else "mock"
        provider = os.getenv("INFERENCE_PROVIDER", default_provider).strip().lower()
        if provider not in {"mock", "local"}:
            raise ValueError("INFERENCE_PROVIDER debe ser mock o local.")
        default_model = bundled_model if getattr(sys, "frozen", False) else Path("models/vector_urosight/best.pt")
        return cls(provider, Path(os.getenv("LOCAL_MODEL_PATH", str(default_model))), _imgsz_from_env(),
                   _boolean_from_env("LOCAL_MODEL_AUGMENT", True),
                   _confidence_from_env(), _max_detections_from_env())


class _EnvironmentSettings:
    """Validate configuration inside the startup error handler, not at import."""
    def __getattr__(self, name):
        return getattr(Settings.from_environment(), name)


settings = _EnvironmentSettings()
