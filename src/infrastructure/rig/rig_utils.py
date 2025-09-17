"""Utilidades para aplicar rotaciones a joints en Panda3D."""

from __future__ import annotations

from typing import Dict, Tuple

from panda3d.core import LVecBase3f

from domain.config import AXIS_CFG, FIXED_OVERRIDES
from domain.metrics import angle2d


def fixed_hpr(
    base_hpr: Dict[str, Tuple[float, float, float]],
    jname: str,
) -> Tuple[float, float, float]:
    """Devuelve el HPR base con overrides fijos aplicados.

    Args:
        base_hpr: Diccionario {joint: (H, P, R)}.
        jname: Nombre del joint.

    Returns:
        Tupla (H, P, R) con overrides aplicados.
    """
    h0, p0, r0 = base_hpr.get(jname, (0.0, 0.0, 0.0))
    overrides = FIXED_OVERRIDES.get(jname, {})

    return (
        h0 if overrides.get("H") is None else float(overrides["H"]),
        p0 if overrides.get("P") is None else float(overrides["P"]),
        r0 if overrides.get("R") is None else float(overrides["R"]),
    )


def set_axis_angle(
    np_joint,
    jname: str,
    axis: str,
    angle_deg: float,
    base_hpr: Dict[str, Tuple[float, float, float]],
) -> None:
    """Aplica un ángulo en un eje específico de un joint.

    Args:
        np_joint: Nodo de Panda3D que representa el joint.
        jname: Nombre del joint.
        axis: Eje ("H", "P" o "R").
        angle_deg: Ángulo en grados.
        base_hpr: HPR base para el joint.
    """
    h_fixed, p_fixed, r_fixed = fixed_hpr(base_hpr, jname)

    if axis == "H":
        np_joint.setHpr(LVecBase3f(angle_deg, p_fixed, r_fixed))
    elif axis == "P":
        np_joint.setHpr(LVecBase3f(h_fixed, angle_deg, r_fixed))
    else:
        np_joint.setHpr(LVecBase3f(h_fixed, p_fixed, angle_deg))


def apply_vec_to_joint(
    np_joint,
    jname: str,
    p_a: Tuple[float, float],
    p_b: Tuple[float, float],
    base_hpr: Dict[str, Tuple[float, float, float]],
    scale: float = 1.0,
) -> None:
    """Aplica la rotación derivada de dos puntos a un joint.

    Args:
        np_joint: Nodo de Panda3D que representa el joint.
        jname: Nombre del joint.
        p_a: Punto A (x, y).
        p_b: Punto B (x, y).
        base_hpr: HPR base del joint.
        scale: Factor de escala para el ángulo.
    """
    if not np_joint or not p_a or not p_b:
        return

    axis, sign, offset = AXIS_CFG.get(jname, ("H", +1, 0))
    angle = angle2d(p_a, p_b) * scale
    set_axis_angle(np_joint, jname, axis, sign * angle + offset, base_hpr)
