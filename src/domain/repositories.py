"""
Definición de interfaces abstractas para modelos de pose e integración de métricas.

Incluye las abstracciones que deben implementar los modelos de pose
y los sinks de métricas para almacenar o recuperar información.
"""

from abc import ABC, abstractmethod
from typing import Any

from .entities import InferenceResult, Metrics


class PoseModel(ABC):
    """
    Interfaz base para un modelo de detección de poses.
    """

    @abstractmethod
    def infer(self, bgr_image: Any) -> InferenceResult:
        """
        Ejecuta la inferencia sobre una imagen en formato BGR.

        Args:
            bgr_image (Any): Imagen en formato BGR (ej. array de NumPy).

        Returns:
            InferenceResult: Resultado con las poses detectadas.
        """
        pass


class MetricsSink(ABC):
    """
    Interfaz base para un consumidor de métricas del servidor.
    """

    @abstractmethod
    def push(self, m: Metrics) -> None:
        """
        Inserta una nueva métrica en el sink.

        Args:
            m (Metrics): Métrica a almacenar.
        """
        pass

    @abstractmethod
    def snapshot(self, n: int = 120) -> Any:
        """
        Devuelve un snapshot de las últimas métricas almacenadas.

        Args:
            n (int, opcional): Número máximo de métricas a incluir
                en el snapshot. Por defecto 120.

        Returns:
            Any: Representación de las métricas almacenadas.
        """
        pass
