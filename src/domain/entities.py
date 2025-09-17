"""Entidades principales del dominio: Keypoint, Pose y Angles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Keypoint:
    """Representa un keypoint detectado en una persona.

    Args:
        x: Coordenada X del keypoint.
        y: Coordenada Y del keypoint.
        conf: Confianza asociada al keypoint [0,1].
    """

    x: float
    y: float
    conf: float


@dataclass
class Pose:
    """Pose humana en formato COCO de 17 puntos.

    Args:
        keypoints: Lista de 17 `Keypoint` que describen la pose.
    """

    keypoints: List[Keypoint]


@dataclass
class Angles:
    """Ángulos calculados en grados para distintos segmentos.

    Claves libres: `"L_upperarm"`, `"R_elbow_rel"`, etc.

    Args:
        values: Diccionario {nombre_segmento: ángulo_en_grados}.
    """

    values: Dict[str, float]
