"""Caso de uso: procesa un frame, estima poses y actualiza métricas."""

from __future__ import annotations

import time
from typing import Optional

import numpy as np

from domain.entities import Pose
from domain.metrics import kp_metrics
from domain.ports import MetricsStore, PoseEstimator


class ProcessFrameUseCase:
    """Toma un frame BGR, corre pose y devuelve métricas.

    - Calcula FPS con un suavizado exponencial.
    - Ejecuta inferencia de poses usando el `PoseEstimator`.
    - Calcula métricas básicas (confianza media, keypoints visibles).
    - Escribe métricas en el `MetricsStore`.
    """

    def __init__(
        self,
        pose_estimator: PoseEstimator,
        metrics_store: MetricsStore,
    ) -> None:
        """Inicializa el caso de uso.

        Args:
            pose_estimator: Componente que infiere poses desde frames BGR.
            metrics_store: Componente que persiste métricas.
        """
        self.pose_estimator = pose_estimator
        self.metrics_store = metrics_store

        self._fps_ema = 0.0
        self._ema_a = 0.9
        self._t_prev = time.perf_counter()

        # Inicializa archivo/store con métricas vacías
        self.metrics_store.init_empty()

    def _update_fps(self) -> None:
        """Actualiza FPS mediante promedio móvil exponencial."""
        now = time.perf_counter()
        dt = max(1e-6, now - self._t_prev)
        self._t_prev = now

        inst = 1.0 / dt
        self._fps_ema = self._ema_a * self._fps_ema + (1 - self._ema_a) * inst

    def __call__(self, frame_bgr: np.ndarray) -> dict:
        """Procesa un frame BGR y devuelve métricas.

        Args:
            frame_bgr: Imagen en formato BGR (numpy array).

        Returns:
            dict: Métricas calculadas, con claves:
                - ts (timestamp)
                - persons (número de personas detectadas)
                - fps (frames por segundo estimados)
                - mean_kp_conf (confianza media keypoints)
                - visible_ratio (fracción visible de keypoints)
                - visible_count (cantidad de keypoints visibles)
                - pose_conf (confianza de la primera detección)
                - angles (diccionario de ángulos)
        """
        self._update_fps()
        poses, first_conf = self.pose_estimator.infer(frame_bgr)
        num_persons = len(poses)

        metrics = {
            "ts": time.time(),
            "persons": num_persons,
            "fps": self._fps_ema,
            "mean_kp_conf": 0.0,
            "visible_ratio": 0.0,
            "visible_count": 0,
            "pose_conf": (
                float(first_conf) if first_conf is not None else None
            ),
            "angles": {},
        }

        if num_persons > 0:
            # Calcula métricas de la primera persona
            kps = [(kp.x, kp.y, kp.conf) for kp in poses[0].keypoints]
            mean_conf, vis_ratio, vis_count = kp_metrics(kps)
            metrics.update(
                {
                    "mean_kp_conf": mean_conf,
                    "visible_ratio": vis_ratio,
                    "visible_count": vis_count,
                }
            )

        self.metrics_store.write(metrics)
        return metrics
