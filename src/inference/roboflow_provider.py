import base64
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

from src.domain.models import BoundingBox, Detection, ImageAnalysis
from src.inference.base import InferenceProvider


class RoboflowProvider(InferenceProvider):
    """Object detection through Roboflow's official hosted REST endpoint."""

    display_name = "Roboflow remoto (REST)"
    is_simulated = False
    _BASE_URL = "https://detect.roboflow.com"

    def __init__(
        self,
        api_key: str,
        model_id: str,
        confidence: float = 0.25,
        timeout: tuple[float, float] = (10.0, 60.0),
        session: Any | None = None,
        diagnostic: bool = False,
    ) -> None:
        if not api_key:
            raise ValueError("ROBOFLOW_API_KEY no está configurada.")
        project, separator, version = model_id.strip().rpartition("/")
        if not separator or not project or not version:
            raise ValueError("ROBOFLOW_MODEL_ID debe usar el formato proyecto/versión.")
        if not 0 <= confidence <= 1:
            raise ValueError("El umbral de Roboflow debe estar entre 0 y 1.")
        if session is None:
            import requests
            session = requests.Session()
        self._session = session
        self._api_key = api_key
        self._confidence = confidence
        self.confidence_threshold = confidence
        self._timeout = timeout
        self._model_id = model_id.strip()
        self._diagnostic = diagnostic
        self._endpoint = f"{self._BASE_URL}/{quote(project, safe='')}/{quote(version, safe='')}"

    def predict(self, image_path: Path) -> ImageAnalysis:
        if not image_path.is_file():
            raise FileNotFoundError(f"No existe la imagen para inferencia: {image_path}")
        start = time.perf_counter()
        try:
            encoded_image = base64.b64encode(image_path.read_bytes())
            response = self._session.post(
                self._endpoint,
                params={"api_key": self._api_key, "confidence": round(self._confidence * 100), "format": "json"},
                data=encoded_image,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=self._timeout,
            )
        except Exception as exc:
            self._raise_transport_error(exc)

        status = int(getattr(response, "status_code", 0))
        if status in {401, 403}:
            raise PermissionError("Roboflow rechazó la API key o no autorizó el acceso al modelo.")
        if status == 404:
            raise LookupError("El modelo o la versión configurada no están disponibles en Roboflow.")
        if status in {408, 504}:
            raise TimeoutError("Roboflow agotó el tiempo de espera de la inferencia.")
        if status == 429:
            raise RuntimeError("Roboflow rechazó temporalmente la solicitud por límite de uso.")
        if status < 200 or status >= 300:
            raise RuntimeError(f"Roboflow devolvió un error HTTP {status}.")
        try:
            payload = response.json()
        except Exception as exc:
            raise ValueError("Roboflow devolvió una respuesta que no es JSON válido.") from exc
        detections = self._parse_predictions(payload, self._model_id, self._confidence, image_path.name)
        return ImageAnalysis(image_path=image_path, detections=detections,
                             inference_ms=(time.perf_counter() - start) * 1000,
                             raw_response=payload if self._diagnostic else None)

    @staticmethod
    def _raise_transport_error(exc: Exception) -> None:
        # Import lazily so mock/local operation never loads optional network packages.
        try:
            import requests
        except ImportError:
            raise RuntimeError("La integración Roboflow REST requiere instalar requests.") from None
        if isinstance(exc, requests.Timeout):
            raise TimeoutError("Se agotó el tiempo de conexión con Roboflow.") from None
        if isinstance(exc, requests.ConnectionError):
            raise ConnectionError("No fue posible conectar con Roboflow.") from None
        if isinstance(exc, OSError):
            raise ConnectionError("No fue posible preparar o enviar la imagen a Roboflow.") from None
        raise RuntimeError("Falló la solicitud REST a Roboflow.") from None

    @staticmethod
    def _parse_predictions(payload: Any, model_id: str = "", threshold: float = 0.0,
                           source_image: str = "") -> list[Detection]:
        if not isinstance(payload, dict) or not isinstance(payload.get("predictions"), list):
            raise ValueError("Roboflow devolvió una respuesta sin una lista de predicciones válida.")
        detections: list[Detection] = []
        required = ("class", "confidence", "x", "y", "width", "height")
        for index, item in enumerate(payload["predictions"], start=1):
            if not isinstance(item, dict) or any(name not in item for name in required):
                raise ValueError(f"La predicción {index} de Roboflow tiene una estructura inesperada.")
            try:
                detections.append(Detection(
                    class_name=str(item["class"]),
                    confidence=float(item["confidence"]),
                    bbox=BoundingBox(x=float(item["x"]), y=float(item["y"]),
                                     width=float(item["width"]), height=float(item["height"])),
                    raw_class=str(item["class"]), model_id=model_id,
                    inference_threshold=threshold, source_image=source_image,
                    detection_id=str(item.get("detection_id") or f"{source_image}:{index}"),
                ))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"La predicción {index} de Roboflow contiene valores inválidos.") from exc
        return detections
