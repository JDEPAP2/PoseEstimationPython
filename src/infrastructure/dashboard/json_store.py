"""Almacén de métricas en archivo JSON con escritura atómica."""

from __future__ import annotations

import json
import os
import time
from typing import Dict, Any


class JsonMetricsStore:
    """Responsabilidad única: persistir métricas en un archivo JSON."""

    def __init__(self, json_path: str) -> None:
        """Inicializa el repositorio.

        Args:
            json_path: Ruta al archivo JSON donde se guardarán las métricas.
        """
        self.json_path = json_path

    def init_empty(self) -> None:
        """Crea un archivo JSON inicial con métricas vacías."""
        self.write(
            {
                "ts": time.time(),
                "persons": 0,
                "fps": 0.0,
                "mean_kp_conf": 0.0,
                "visible_ratio": 0.0,
                "visible_count": 0,
                "pose_conf": None,
                "angles": {},
            }
        )

    def write(self, metrics: Dict[str, Any]) -> None:
        """Escribe las métricas en el archivo JSON de manera atómica.

        Args:
            metrics: Diccionario con métricas a persistir.
        """
        tmp = self.json_path + ".tmp"
        os.makedirs(os.path.dirname(self.json_path), exist_ok=True)

        with open(tmp, "w", encoding="utf-8") as file:
            json.dump(metrics, file)

        try:
            os.replace(tmp, self.json_path)
        except PermissionError:
            with open(self.json_path, "w", encoding="utf-8") as file:
                json.dump(metrics, file)
        finally:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
