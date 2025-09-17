"""Utilidades para dibujar poses sobre un frame de OpenCV."""

from typing import List, Tuple

import cv2

from domain.config import KP_THRES, SKELETON
from domain.entities import Pose


def draw_pose_overlay(
    frame_bgr,
    poses: List[Pose],
    th: float = KP_THRES,
) -> None:
    """Dibuja esqueletos y keypoints sobre un frame BGR.

    Args:
        frame_bgr: Imagen en formato BGR (OpenCV) sobre la que se dibuja.
        poses: Lista de objetos Pose con keypoints detectados.
        th: Umbral mínimo de confianza para mostrar keypoints y enlaces.
    """
    if not poses:
        return

    for pose in poses:
        keypoints: List[Tuple[int, int, float]] = [
            (int(k.x), int(k.y), float(k.conf))
            for k in pose.keypoints
        ]

        # Dibujar conexiones del esqueleto
        for a, b in SKELETON:
            xa, ya, ca = keypoints[a]
            xb, yb, cb = keypoints[b]
            if ca >= th and cb >= th:
                cv2.line(
                    frame_bgr,
                    (xa, ya),
                    (xb, yb),
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA,
                )

        # Dibujar puntos clave
        for x, y, conf in keypoints:
            if conf >= th:
                cv2.circle(
                    frame_bgr,
                    (x, y),
                    3,
                    (255, 0, 0),
                    -1,
                    cv2.LINE_AA,
                )
