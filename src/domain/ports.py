"""Definiciones de puertos (Protocols) para la arquitectura del proyecto."""

from __future__ import annotations

from typing import List, Optional, Protocol, Tuple

import numpy as np

from domain.entities import Pose


class Camera(Protocol):
    """Interfaz de cámara para captura de frames."""

    def open(self) -> None:
        """Abre el dispositivo de cámara.

        Returns:
            None
        """
        ...

    def read(self) -> Tuple[bool, "np.ndarray"]:
        """Lee un frame del dispositivo.

        Returns:
            Tuple[bool, np.ndarray]: (ok, frame BGR).
                - ok: True si la lectura fue exitosa.
                - frame: Imagen en formato BGR (numpy array).
        """
        ...

    def release(self) -> None:
        """Libera el recurso de la cámara.

        Returns:
            None
        """
        ...


class PoseEstimator(Protocol):
    """Interfaz para estimadores de pose humana."""

    def infer(
        self,
        frame_bgr: "np.ndarray",
    ) -> Tuple[List[Pose], Optional[float]]:
        """Ejecuta inferencia de poses sobre un frame BGR.

        Args:
            frame_bgr: Imagen en formato BGR (numpy array).

        Returns:
            Tuple[List[Pose], Optional[float]]:
                - Lista de poses detectadas (0..N).
                - Confianza de la primera detección (si existe).
        """
        ...


class RigController(Protocol):
    """Interfaz del controlador de rig 3D."""

    def apply_pose(
        self,
        pose: Pose,
        boxes_conf: Optional[float],
    ) -> dict:
        """Aplica una pose al rig y devuelve métricas.

        Args:
            pose: Pose detectada con keypoints válidos.
            boxes_conf: Confianza del bounding box (opcional).

        Returns:
            dict: Métricas calculadas (p. ej., ángulos por segmento).
        """
        ...


class MetricsStore(Protocol):
    """Interfaz de persistencia de métricas."""

    def init_empty(self) -> None:
        """Inicializa el almacenamiento con métricas vacías.

        Returns:
            None
        """
        ...

    def write(self, metrics: dict) -> None:
        """Persiste un diccionario de métricas.

        Args:
            metrics: Estructura con métricas a guardar.

        Returns:
            None
        """
        ...