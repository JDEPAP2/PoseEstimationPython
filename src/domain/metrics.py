"""Funciones auxiliares para métricas angulares y keypoints."""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

import numpy as np

from domain.config import KP_THRES


def angle2d(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calcula el ángulo 2D (en grados) entre dos puntos.

    Args:
        p1: Punto (x, y) inicial.
        p2: Punto (x, y) final.

    Returns:
        Ángulo en grados en el rango [-180, 180].
    """
    (x1, y1), (x2, y2) = p1, p2
    dx, dy = (x2 - x1), (y2 - y1)
    dy = -dy  # invertir eje Y para convención gráfica
    return math.degrees(math.atan2(dy, dx))


def ang_norm(angle: float) -> float:
    """Normaliza un ángulo al rango [-180, 180].

    Args:
        angle: Ángulo en grados.

    Returns:
        Ángulo normalizado.
    """
    return (angle + 180.0) % 360.0 - 180.0


def ang_diff(a: float, b: float) -> float:
    """Calcula la diferencia normalizada entre dos ángulos.

    Args:
        a: Ángulo A en grados.
        b: Ángulo B en grados.

    Returns:
        Diferencia angular normalizada [-180, 180].
    """
    return ang_norm(a - b)


def safe_pt(
    kps: List[Tuple[float, float, float]],
    idx: int,
    th: float = KP_THRES,
) -> Optional[Tuple[float, float]]:
    """Devuelve un punto (x, y) si su confianza ≥ umbral.

    Args:
        kps: Lista de keypoints [(x, y, conf), ...].
        idx: Índice del keypoint a evaluar.
        th: Umbral mínimo de confianza.

    Returns:
        (x, y) si la confianza es suficiente, None en caso contrario.
    """
    x, y, c = kps[idx]
    return (float(x), float(y)) if float(c) >= th else None


def kp_metrics(
    person_kps: List[Tuple[float, float, float]],
    kp_th: float = KP_THRES,
) -> Tuple[float, float, int]:
    """Calcula métricas básicas a partir de keypoints de una persona.

    Args:
        person_kps: Lista [(x, y, conf), ...] de 17 keypoints.
        kp_th: Umbral de confianza.

    Returns:
        Tuple con:
            - mean_conf (float): confianza media de keypoints visibles.
            - ratio (float): proporción de keypoints visibles [0,1].
            - visible (int): número de keypoints visibles.
    """
    confs = [float(c) for (_, _, c) in person_kps if float(c) >= kp_th]
    visible = len(confs)
    mean_conf = float(np.mean(confs)) if confs else 0.0
    ratio = visible / 17.0
    return mean_conf, ratio, visible
