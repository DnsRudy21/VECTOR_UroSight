from dataclasses import dataclass
import os
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
    raw = os.getenv("CONFIDENCE_THRESHOLD", "0.25")
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError("CONFIDENCE_THRESHOLD debe ser un número entre 0 y 1.") from exc
    if not 0 <= value <= 1:
        raise ValueError("CONFIDENCE_THRESHOLD debe estar entre 0 y 1.")
    return value


@dataclass(frozen=True)
class Settings:
    inference_provider: str
    roboflow_api_key: str
    roboflow_model_id: str
    local_model_path: Path
    confidence_threshold: float
    roboflow_diagnostic: bool

    @classmethod
    def from_environment(cls) -> "Settings":
        bundled_model = application_root() / "models" / "vector_urosight" / "best.pt"
        default_provider = "local" if getattr(sys, "frozen", False) and bundled_model.is_file() else "mock"
        provider = os.getenv("INFERENCE_PROVIDER", default_provider).strip().lower()
        if provider not in {"mock", "local", "roboflow"}:
            raise ValueError("INFERENCE_PROVIDER debe ser mock, local o roboflow.")
        default_model = bundled_model if getattr(sys, "frozen", False) else Path("models/vector_urosight/best.pt")
        return cls(provider, os.getenv("ROBOFLOW_API_KEY", ""),
                   os.getenv("ROBOFLOW_MODEL_ID", "urine-sediment-yolov8/1"),
                   Path(os.getenv("LOCAL_MODEL_PATH", str(default_model))), _confidence_from_env(),
                   os.getenv("ROBOFLOW_DIAGNOSTIC", "false").strip().lower() in {"1", "true", "yes"})


settings = Settings.from_environment()
