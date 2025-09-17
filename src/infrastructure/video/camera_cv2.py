"""Implementación de cámara usando OpenCV."""

from __future__ import annotations

from typing import Tuple

import cv2

from domain.ports import Camera


class Cv2Camera(Camera):
    """Adaptador de cámara basado en OpenCV."""

    def __init__(self, cam_index: int = 0) -> None:
        """Inicializa la cámara.

        Args:
            cam_index: Índice de la cámara en el sistema.
        """
        self.cam_index = cam_index
        self.cap: cv2.VideoCapture | None = None

    def open(self) -> None:
        """Abre la cámara especificada en `cam_index`."""
        self.cap = cv2.VideoCapture(self.cam_index)
        if not self.cap.isOpened():
            raise RuntimeError("No se pudo abrir la cámara.")

    def read(self) -> Tuple[bool, any]:
        """Lee un frame de la cámara.

        Returns:
            Tupla (ok, frame) como en `cv2.VideoCapture.read()`.
        """
        if self.cap is None:
            raise RuntimeError("La cámara no está abierta.")
        return self.cap.read()

    def release(self) -> None:
        """Libera el recurso de la cámara."""
        try:
            if self.cap is not None:
                self.cap.release()
        except Exception:
            pass
