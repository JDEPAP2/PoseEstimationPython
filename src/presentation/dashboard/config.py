"""Configuración global del dashboard de métricas de pose."""

from pathlib import Path

# --- Archivos y rutas ---
DATA_FILE = Path("outputs/dashboards/pose_metrics.json")

# --- Parámetros de refresco e históricos ---
REFRESH_MS = 250
MAX_POINTS = 400
DECIMALS = 3

# --- Columnas estándar del histórico ---
HIST_COLS = [
    "t",
    "fps",
    "mean_kp_conf",
    "visible_ratio",
    "visible_count",
    "pose_conf",
]

# --- Estructura vacía de métricas ---
EMPTY_METRICS = {
    "ts": 0.0,
    "persons": 0,
    "fps": 0.0,
    "mean_kp_conf": 0.0,
    "visible_ratio": 0.0,
    "visible_count": 0,
    "pose_conf": None,
    "angles": {},
}
