"""Controlador de rig en Panda3D a partir de keypoints de pose."""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from direct.actor.Actor import Actor
from panda3d.core import LVecBase3f, NodePath

from domain.config import (
    AXIS_CFG,
    FIXED_OVERRIDES,
    JOINT_MAP,
    KP_THRES,
    LANK,
    LELB,
    LHIP,
    LKNE,
    LSHO,
    LWR,
    RANK,
    RELB,
    RHIP,
    RKNE,
    RSHO,
    RWR,
)
from domain.entities import Pose
from domain.metrics import ang_diff, angle2d, safe_pt


class Panda3DRigController:
    """Controla joints del Actor según keypoints (YOLO pose).

    Aplica:
      - Brazos: hombro→codo (upperarm)
      - Codos: (codo→muñeca) relativo a (hombro→codo)
      - Piernas: cadera→rodilla y rodilla→tobillo

    Ejes/offsets toman `AXIS_CFG` y `FIXED_OVERRIDES`.
    """

    def __init__(self, actor: Actor) -> None:
        """Crea el controlador de rig.

        Args:
            actor: Actor de Panda3D ya cargado (GLB/egg/bam).
        """
        self.actor: Actor = actor
        self.controlled: Dict[str, NodePath] = {}
        self._ensure_controlled_joints()
        self.base_hpr: Dict[str, Tuple[float, float, float]] = {
            j: tuple(np_joint.getHpr())
            for j, np_joint in self.controlled.items()
        }

    # ---------- joints ----------
    def _ensure_controlled_joints(self) -> None:
        """Intenta 'modelRoot'; si falla, prueba todas las parts del Actor.

        Args:
            None
        """
        parts = list(self.actor.getPartNames())
        for jname in JOINT_MAP.values():
            np_joint = self.actor.controlJoint(None, "modelRoot", jname)
            if np_joint.isEmpty():
                # Fallback: buscar en parts reales
                for part in parts:
                    np_joint = self.actor.controlJoint(None, part, jname)
                    if not np_joint.isEmpty():
                        break
            if not np_joint.isEmpty():
                self.controlled[jname] = np_joint
            else:
                print(
                    f"[aviso] No pude controlar joint: {jname}. Parts={parts}"
                )

    def _fixed_hpr_for(self, jname: str) -> Tuple[float, float, float]:
        """Devuelve HPR base del joint aplicando overrides fijos.

        Args:
            jname: Nombre del joint.

        Returns:
            Tupla (H, P, R) final para el joint.
        """
        h0, p0, r0 = self.base_hpr.get(jname, (0.0, 0.0, 0.0))
        ov = FIXED_OVERRIDES.get(jname, {})
        h_fix = ov.get("H", None)
        p_fix = ov.get("P", None)
        r_fix = ov.get("R", None)
        return (
            h0 if h_fix is None else float(h_fix),
            p0 if p_fix is None else float(p_fix),
            r0 if r_fix is None else float(r_fix),
        )

    def _set_axis_angle_fixed(
        self,
        jname: str,
        axis: str,
        angle_deg: float,
    ) -> None:
        """Fija el HPR del joint con overrides y un ángulo en un eje.

        Args:
            jname: Nombre del joint.
            axis: Eje a rotar: "H", "P" o "R".
            angle_deg: Ángulo a aplicar en grados.
        """
        np_joint = self.controlled.get(jname)
        if not np_joint:
            return

        h_fixed, p_fixed, r_fixed = self._fixed_hpr_for(jname)

        if axis == "H":
            np_joint.setHpr(LVecBase3f(angle_deg, p_fixed, r_fixed))
        elif axis == "P":
            np_joint.setHpr(LVecBase3f(h_fixed, angle_deg, r_fixed))
        else:
            np_joint.setHpr(LVecBase3f(h_fixed, p_fixed, angle_deg))

    def _apply_vec_to_joint(
        self,
        jname: str,
        p_a: Optional[Tuple[float, float]],
        p_b: Optional[Tuple[float, float]],
        scale: float = 1.0,
    ) -> None:
        """Orienta joint según vector p_a→p_b y configuración de ejes.

        Args:
            jname: Nombre del joint.
            p_a: Punto A (x, y) o None si no hay keypoint válido.
            p_b: Punto B (x, y) o None si no hay keypoint válido.
            scale: Factor de escala del ángulo calculado.
        """
        if not p_a or not p_b:
            return
        axis, sign, offset = AXIS_CFG.get(jname, ("H", +1, 0))
        angle = angle2d(p_a, p_b) * scale
        self._set_axis_angle_fixed(jname, axis, sign * angle + offset)

    # ---------- API principal ----------
    def apply_pose(
        self,
        pose: Pose,
        boxes_conf: Optional[float] = None,
    ) -> Dict[str, Dict[str, float]]:
        """Aplica la pose (primera persona) al rig y devuelve métricas.

        Args:
            pose: Pose con keypoints detectados.
            boxes_conf: Confianza del bounding box (opcional).

        Returns:
            Diccionario con clave "angles" y ángulos por segmento.
        """
        kps = [(kp.x, kp.y, kp.conf) for kp in pose.keypoints]

        p_ls = safe_pt(kps, LSHO, KP_THRES)
        p_rs = safe_pt(kps, RSHO, KP_THRES)
        p_le = safe_pt(kps, LELB, KP_THRES)
        p_re = safe_pt(kps, RELB, KP_THRES)
        p_lw = safe_pt(kps, LWR, KP_THRES)
        p_rw = safe_pt(kps, RWR, KP_THRES)
        p_lh = safe_pt(kps, LHIP, KP_THRES)
        p_rh = safe_pt(kps, RHIP, KP_THRES)
        p_lk = safe_pt(kps, LKNE, KP_THRES)
        p_rk = safe_pt(kps, RKNE, KP_THRES)
        p_la = safe_pt(kps, LANK, KP_THRES)
        p_ra = safe_pt(kps, RANK, KP_THRES)

        out: Dict[str, Dict[str, float]] = {"angles": {}}

        # ----- Brazos: hombro -> codo -----
        if p_ls and p_le:
            a = angle2d(p_ls, p_le)
            self._apply_vec_to_joint(JOINT_MAP["L_UPPERARM"], p_ls, p_le, 1.0)
            out["angles"]["L_upperarm"] = a
        if p_rs and p_re:
            a = angle2d(p_rs, p_re)
            self._apply_vec_to_joint(JOINT_MAP["R_UPPERARM"], p_rs, p_re, 1.0)
            out["angles"]["R_upperarm"] = a

        # ----- Codos: (codo→muñeca) relativo a (hombro→codo) -----
        if p_ls and p_le and p_lw:
            up = angle2d(p_ls, p_le)
            fo = angle2d(p_le, p_lw)
            rel = ang_diff(fo, up)
            jn = JOINT_MAP["L_FOREARM"]
            ax, sign, off = AXIS_CFG.get(jn, ("P", +1, 0))
            self._set_axis_angle_fixed(jn, ax, sign * rel + off)
            out["angles"]["L_elbow_rel"] = rel

        if p_rs and p_re and p_rw:
            up = angle2d(p_rs, p_re)
            fo = angle2d(p_re, p_rw)
            rel = ang_diff(fo, up)
            jn = JOINT_MAP["R_FOREARM"]
            ax, sign, off = AXIS_CFG.get(jn, ("P", +1, 0))
            self._set_axis_angle_fixed(jn, ax, sign * rel + off)
            out["angles"]["R_elbow_rel"] = rel

        # ----- Piernas -----
        if p_lh and p_lk:
            a = angle2d(p_lh, p_lk)
            self._apply_vec_to_joint(JOINT_MAP["L_HIP"], p_lh, p_lk, 0.8)
            out["angles"]["L_hip"] = a

        if p_rh and p_rk:
            a = angle2d(p_rh, p_rk)
            self._apply_vec_to_joint(JOINT_MAP["R_HIP"], p_rh, p_rk, 0.8)
            out["angles"]["R_hip"] = a

        if p_lk and p_la:
            a = angle2d(p_lk, p_la)
            self._apply_vec_to_joint(JOINT_MAP["L_KNEE"], p_lk, p_la, 0.9)
            out["angles"]["L_knee"] = a

        if p_rk and p_ra:
            a = angle2d(p_rk, p_ra)
            self._apply_vec_to_joint(JOINT_MAP["R_KNEE"], p_rk, p_ra, 0.9)
            out["angles"]["R_knee"] = a

        return out
