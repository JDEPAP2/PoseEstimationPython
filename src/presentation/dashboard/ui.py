"""Componentes de UI para el dashboard de poses con Streamlit."""

from __future__ import annotations

from typing import Dict, Optional

import pandas as pd
import streamlit as st


def render_header() -> None:
    """Configura la página y muestra el encabezado del dashboard."""
    # Evita llamar set_page_config múltiples veces (Streamlit lanza warning).
    if not st.session_state.get("_pgcfg_done", False):
        st.set_page_config(page_title="Pose Dashboard", layout="wide")
        st.session_state["_pgcfg_done"] = True

    st.title("Pose Dashboard (YOLO Pose → Rig) — Live métricas")


def render_controls() -> None:
    """Renderiza controles de pausa/reanudación del stream."""
    col_left, col_right, _ = st.columns([1, 1, 2])
    paused = st.session_state.get("paused", False)

    with col_left:
        if st.button("⏸ Pausar", disabled=paused):
            st.session_state.paused = True

    with col_right:
        if st.button("▶️ Reanudar", disabled=not paused):
            st.session_state.paused = False


def render_kpis(row: Dict[str, Optional[float]]) -> None:
    """Muestra KPIs principales a partir de la última fila de métricas.

    Args:
        row: Diccionario con métricas actuales. Claves esperadas:
            - 'fps': frames por segundo (float).
            - 'mean_kp_conf': confianza media de keypoints [0..1].
            - 'visible_count': número de keypoints visibles (int).
            - 'visible_ratio': fracción visible [0..1].
            - 'pose_conf': confianza de la pose [0..1] (opcional).
    """
    k1, k2, k3, k4 = st.columns(4)

    fps_val = float(row.get("fps", 0.0) or 0.0)
    mean_conf = float(row.get("mean_kp_conf", 0.0) or 0.0)
    vis_count = int(row.get("visible_count", 0) or 0)
    vis_ratio = float(row.get("visible_ratio", 0.0) or 0.0)
    pose_conf = row.get("pose_conf")

    k1.metric("FPS", f"{fps_val:.1f}")
    k2.metric("Mean KP Conf", f"{mean_conf * 100:.0f}%")
    k3.metric(
        "Visible KP",
        f"{vis_count}/17 ({vis_ratio * 100:.0f}%)",
    )
    k4.metric(
        "Pose conf",
        "—" if pose_conf is None else f"{float(pose_conf) * 100:.0f}%",
    )


def render_charts(hist: pd.DataFrame) -> None:
    """Dibuja gráficas de series temporales a partir del histórico.

    Args:
        hist: DataFrame con columnas al menos:
            't', 'fps', 'mean_kp_conf', 'visible_ratio', 'pose_conf'.
    """
    if hist.empty:
        st.info("Esperando datos…")
        return

    # Asegurar índice temporal
    df = hist.set_index("t", drop=True)

    # Filtrar solo columnas existentes para evitar KeyError
    def _safe_cols(cols: list[str]) -> list[str]:
        return [c for c in cols if c in df.columns]

    left, right = st.columns(2, gap="small")

    with left:
        st.subheader("FPS")
        fps_cols = _safe_cols(["fps"])
        if fps_cols:
            st.line_chart(df[fps_cols], use_container_width=True)

        st.subheader("Mean KP Conf")
        mk_cols = _safe_cols(["mean_kp_conf"])
        if mk_cols:
            st.line_chart(df[mk_cols], use_container_width=True)

    with right:
        st.subheader("Visible ratio")
        vr_cols = _safe_cols(["visible_ratio"])
        if vr_cols:
            st.line_chart(df[vr_cols], use_container_width=True)

        st.subheader("Pose confidence")
        pc_cols = _safe_cols(["pose_conf"])
        if pc_cols:
            # Asegurar float para evitar problemas con tipos mixtos.
            st.line_chart(
                df[pc_cols].astype(float),
                use_container_width=True,
            )
