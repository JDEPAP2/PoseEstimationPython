"""
Servicio de aplicación para realizar inferencias de pose a partir de imágenes BGR.

Incluye el cálculo de métricas de rendimiento como FPS promedio
(usando un promedio exponencial móvil).
"""

import time
import numpy as np

from ...domain.entities import InferenceResult
from ...domain.usecases.run_inference import RunInference


class PoseService:
    """
    Servicio que orquesta la ejecución de inferencias de pose y
    calcula métricas de rendimiento del servidor.
    """

    def __init__(self, run_inference: RunInference) -> None:
        """
        Inicializa el servicio de pose.

        Args:
            run_inference (RunInference): Caso de uso encargado de ejecutar la inferencia.
        """
        self._run: RunInference = run_inference
        self._last: float = time.time()
        self._ema: float | None = None  # Promedio exponencial móvil de FPS

    def infer_from_bgr(self, bgr: np.ndarray) -> InferenceResult:
        """
        Ejecuta la inferencia de pose sobre una imagen en formato BGR.

        Args:
            bgr (np.ndarray): Imagen en formato BGR (por ejemplo, proveniente de OpenCV).

        Returns:
            InferenceResult: Resultado con las poses detectadas, el tiempo de inferencia
            y el FPS promedio del servidor.
        """
        now: float = time.time()
        dt: float = now - self._last
        self._last = now

        # FPS instantáneo
        server_fps: float = 1.0 / dt if dt > 0 else 0.0

        # Ejecutar inferencia
        result: InferenceResult = self._run(bgr)

        # Calcular FPS suavizado con EMA
        if self._ema is None:
            self._ema = server_fps
        else:
            self._ema = 0.9 * self._ema + 0.1 * server_fps

        return InferenceResult(
            poses=result.poses,
            inference_ms=result.inference_ms,
            server_fps=self._ema,
        )
