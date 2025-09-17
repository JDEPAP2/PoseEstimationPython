"""Aplicación Streamlit para el dashboard de métricas de pose."""

import time

import streamlit as st

from config import DATA_FILE, REFRESH_MS
from repository import MetricsRepository
from state import HistoryBuffer
from ui import (
    render_charts,
    render_controls,
    render_header,
    render_kpis,
)

# ---- Composición (inyección de dependencias de presentación) ----
repo = MetricsRepository(DATA_FILE)

if "histbuf" not in st.session_state:
    st.session_state.histbuf = HistoryBuffer()

histbuf: HistoryBuffer = st.session_state.histbuf


def tick() -> None:
    """Lee métricas, actualiza buffer histórico y renderiza KPIs + gráficas."""
    metrics = repo.read_metrics()
    hist = histbuf.add_metrics(metrics)
    row = histbuf.current_row()
    render_kpis(row)
    render_charts(hist)


# ------------------------ Página ------------------------
if "paused" not in st.session_state:
    st.session_state.paused = False

render_header()
render_controls()

# Ciclo simple de auto-actualización sin while True ni threads
if not st.session_state.paused:
    tick()
    time.sleep(REFRESH_MS / 1000.0)
    st.rerun()
else:
    st.info("⏸ Pausado")
