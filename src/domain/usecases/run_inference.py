"""
Caso de uso: ejecutar inferencia sobre una imagen utilizando un modelo de pose.
"""

from typing import Any

from ..entities import InferenceResult
from ..repositories import PoseModel


class RunInference:
    """
    Encapsula la ejecución de la inferencia de poses usando un modelo dado.
    """

    def __init__(self, model: PoseModel) -> None:
        """
        Inicializa el caso de uso con un modelo de pose.

        Args:
            model (PoseModel): Instancia concreta de un modelo de pose.
        """
        self._model: PoseModel = model

    def __call__(self, bgr_image: Any) -> InferenceResult:
        """
        Ejecuta la inferencia sobre una imagen en formato BGR.

        Args:
            bgr_image (Any): Imagen en formato BGR (ej. `numpy.ndarray` de OpenCV).

        Returns:
            InferenceResult: Resultado de la inferencia con poses detectadas.
        """
        return self._model.infer(bgr_image)
