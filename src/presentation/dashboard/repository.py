"""Repositorio de métricas.

Responsabilidad única:
- Leer métricas crudas desde un archivo JSON.
- En caso de error, devolver un diccionario vacío con timestamp.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict

from config import EMPTY_METRICS


class MetricsRepository:
    """Repositorio para leer métricas crudas del origen (JSON)."""

    def __init__(self, data_file: Path) -> None:
        """Inicializa el repositorio.

        Args:
            data_file: Ruta al archivo JSON con métricas.
        """
        self.data_file = data_file

    def read_metrics(self) -> Dict[str, Any]:
        """Lee métricas desde el archivo JSON.

        Returns:
            Diccionario con métricas. Si ocurre un error,
            devuelve una copia de EMPTY_METRICS con timestamp.
        """
        try:
            with open(self.data_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, json.JSONDecodeError):
            metrics = dict(EMPTY_METRICS)
            metrics["ts"] = time.time()
            return metrics
