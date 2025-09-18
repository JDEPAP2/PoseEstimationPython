"""Buffer de histórico para métricas de pose.

Responsabilidad única:
- Mantener un DataFrame con las métricas más recientes.
- Normalizar y redondear valores con tolerancia a entradas ruidosas.
"""

from __future__ import annotations

import warnings

warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message=".*DataFrame concatenation with empty or all-NA entries.*"
)

from typing import Any, Dict, List, Optional

import pandas as pd

from config import DECIMALS, HIST_COLS, MAX_POINTS


def clamp01(x: Any) -> float:
    """Restringe un valor al rango [0.0, 1.0]."""
    try:
        val = float(x)
    except Exception:
        return 0.0
    if val < 0.0:
        return 0.0
    if val > 1.0:
        return 1.0
    return val


class HistoryBuffer:
    """Mantiene y normaliza el histórico de métricas."""

    def __init__(
        self,
        cols: Optional[List[str]] = None,
        max_points: int = MAX_POINTS,
        decimals: int = DECIMALS,
    ) -> None:
        """Inicializa el buffer.

        Args:
            cols: Columnas esperadas del histórico.
            max_points: Número máximo de filas a retener.
            decimals: Decimales para redondeo de valores numéricos.
        """
        self.cols = cols or HIST_COLS
        self.max_points = int(max_points)
        self.decimals = int(decimals)
        self.df = pd.DataFrame(columns=self.cols)

    def add_metrics(self, metrics: Dict[str, Any]) -> pd.DataFrame:
        """Agrega una fila de métricas y devuelve el DataFrame actualizado.

        Args:
            metrics: Diccionario con claves:
                - 'ts', 'fps', 'mean_kp_conf', 'visible_ratio',
                  'visible_count', 'pose_conf' (opcional)

        Returns:
            DataFrame con las últimas `max_points` filas.
        """
        row = {
            "t": float(metrics.get("ts", 0.0)),
            "fps": float(metrics.get("fps", 0.0)),
            "mean_kp_conf": clamp01(metrics.get("mean_kp_conf", 0.0)),
            "visible_ratio": clamp01(metrics.get("visible_ratio", 0.0)),
            "visible_count": int(metrics.get("visible_count", 0)),
            "pose_conf": (
                float(metrics["pose_conf"])
                if metrics.get("pose_conf") is not None
                else None
            ),
        }

        self.df = pd.concat(
            [self.df, pd.DataFrame([row])],
            ignore_index=True,
        ).tail(self.max_points)

        # Casting/round seguro en columnas numéricas
        num_cols = ["fps", "mean_kp_conf", "visible_ratio", "pose_conf"]
        for col in num_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(
                    self.df[col],
                    errors="coerce",
                ).round(self.decimals)

        return self.df

    def current_row(self) -> Dict[str, Any]:
        """Devuelve la última fila como diccionario (o {} si no hay datos)."""
        if self.df.empty:
            return {}
        return self.df.iloc[-1].to_dict()
