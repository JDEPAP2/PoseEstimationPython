"""
Definiciones de estructuras de datos para resultados de inferencia de pose.

Incluye representaciones de keypoints, poses individuales y métricas de servidor.
"""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Keypoint:
    """
    Representa un punto clave detectado en una pose.

    Attributes:
        x (float): Coordenada X normalizada o en píxeles.
        y (float): Coordenada Y normalizada o en píxeles.
        c (float): Nivel de confianza del keypoint (0.0 - 1.0).
    """
    x: float
    y: float
    c: float  # Confidence


@dataclass
class Pose:
    """
    Representa una pose detectada en una imagen.

    Attributes:
        keypoints (List[Keypoint]): Lista de keypoints de la pose.
        bbox (Tuple[float, float, float, float]): Bounding box en formato (x, y, w, h).
        score (float): Puntuación de confianza general de la pose.
    """
    keypoints: List[Keypoint]
    bbox: Tuple[float, float, float, float]
    score: float


@dataclass
class InferenceResult:
    """
    Resultado de una inferencia realizada por el modelo.

    Attributes:
        poses (List[Pose]): Poses detectadas en la imagen.
        inference_ms (float): Tiempo de inferencia en milisegundos.
        server_fps (float): Rendimiento del servidor en frames por segundo.
    """
    poses: List[Pose]
    inference_ms: float
    server_fps: float


@dataclass
class Metrics:
    """
    Métricas de desempeño del servidor durante la inferencia.

    Attributes:
        t (float): Marca de tiempo en segundos desde época (epoch).
        inference_ms (float): Tiempo medio de inferencia por frame.
        server_fps (float): Frames por segundo alcanzados.
        mean_kp_conf (float): Confianza media de los keypoints detectados.
    """
    t: float
    inference_ms: float
    server_fps: float
    mean_kp_conf: float
