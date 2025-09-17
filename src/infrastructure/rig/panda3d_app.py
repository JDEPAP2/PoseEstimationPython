"""Vista Panda3D: modelo GLB + cámara con overlay y envío de métricas."""

from __future__ import annotations

from typing import List, Tuple

import cv2
import numpy as np
from direct.actor.Actor import Actor
from direct.gui.DirectGui import DirectLabel
from direct.gui.OnscreenImage import OnscreenImage
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    AmbientLight,
    DirectionalLight,
    Texture,
    Vec4,
    WindowProperties,
)

from domain.entities import Pose
from domain.ports import Camera
from infrastructure.rig.panda3d_rig import Panda3DRigController
from presentation.overlay.pose_overlay import draw_pose_overlay


class Panda3DView(ShowBase):
    """Ventana única que combina rig 3D, cámara y métricas/hud."""

    def __init__(
        self,
        glb_path: str,
        camera: Camera,
        usecase,
        corner_scale: float = 0.33,
    ) -> None:
        """Inicializa la vista y registra la tarea de actualización.

        Args:
            glb_path: Ruta al modelo GLB del rig.
            camera: Implementación de `Camera` para capturar frames.
            usecase: Caso de uso que calcula/infiere métricas de pose.
            corner_scale: Escala del recuadro de la cámara en pantalla.
        """
        super().__init__()

        self.corner_scale = float(corner_scale)

        self._setup_window()
        self._setup_scene(glb_path)
        self._setup_lights()
        self._setup_hud()

        self.camera_dev = camera
        self.camera_dev.open()

        self.usecase = usecase
        self.rig = Panda3DRigController(self.actor)

        self.tex: Texture | None = None
        self.osi: OnscreenImage | None = None

        self.accept("escape", self.userExit)
        self.taskMgr.add(self.update, "update")

    # -------- setup --------
    def _setup_window(self) -> None:
        """Configura el tamaño, título y fondo de la ventana.

        Args:
            None
        """
        props = WindowProperties()
        props.setTitle("Rig + Posenet")
        props.setSize(1280, 720)
        self.win.requestProperties(props)
        self.setBackgroundColor(0.055, 0.067, 0.09, 1)

    def _setup_scene(self, glb_path: str) -> None:
        """Carga el actor GLB y ajusta cámara orbital básica.

        Args:
            glb_path: Ruta al modelo GLB a cargar en el Actor.
        """
        self.actor = Actor(glb_path)
        self.actor.reparentTo(self.render)
        self.disableMouse()

        self.actor.setScale(2.0)
        self.actor.setPos(0, 4, -2)

        self.camera.setPos(0, -10, 2)
        self.camera.lookAt(0, 0, 1)

    def _setup_lights(self) -> None:
        """Iluminación básica: luz ambiente + luz direccional (key).

        Args:
            None
        """
        amb = AmbientLight("amb")
        amb.setColor(Vec4(0.4, 0.4, 0.45, 1))
        self.render.setLight(self.render.attachNewNode(amb))

        key = DirectionalLight("key")
        key.setColor(Vec4(0.9, 0.9, 0.9, 1))
        key_np = self.render.attachNewNode(key)
        key_np.setHpr(-30, -20, 0)
        self.render.setLight(key_np)

    def _setup_hud(self) -> None:
        """Texto superior con ayuda y URL del dashboard.

        Args:
            None
        """
        DirectLabel(
            text="ESC para salir — Dashboard: http://localhost:8501",
            scale=0.045,
            pos=(0, 0, 0.92),
            frameColor=(0, 0, 0, 0),
            text_fg=(1, 1, 1, 1),
        )

    def _ensure_texture(self, width: int, height: int) -> None:
        """Crea textura/HUD para el video si aún no existe.

        Args:
            width: Ancho del frame de cámara en píxeles.
            height: Alto del frame de cámara en píxeles.
        """
        if self.tex is not None:
            return

        self.tex = Texture()
        self.tex.setup2dTexture(
            width,
            height,
            Texture.T_unsigned_byte,
            Texture.F_rgb,
        )

        aspect = height / float(width)
        self.osi = OnscreenImage(
            image=self.tex,
            pos=(
                1.0 - self.corner_scale,
                0,
                -0.95 + (self.corner_scale * aspect),
            ),
            scale=(self.corner_scale, 1, self.corner_scale * aspect),
            parent=self.aspect2d,
        )
        # Transparencia para mezclar con el fondo.
        self.osi.setTransparency(True)

    # -------- loop --------
    def update(self, task):
        """Captura, infiere, dibuja overlay, actualiza métricas y blitea.

        Args:
            task: Objeto `Task` del task manager de Panda3D.

        Returns:
            `task.cont` para continuar la tarea en el siguiente frame.
        """
        ok, frame = self._read_frame()
        if not ok:
            return task.cont

        poses, first_conf = self._infer(frame)
        draw_pose_overlay(frame, poses)

        metrics = self._update_metrics(frame, poses, first_conf)
        self._draw_hud_text(frame, metrics)
        self._blit_to_texture(frame)

        return task.cont

    # -------- helpers pequeños --------
    def _read_frame(self) -> Tuple[bool, "np.ndarray"]:
        """Lee un frame de la cámara y garantiza textura HUD.

        Args:
            None

        Returns:
            Tupla (ok, frame). Si `ok` es False, `frame` es indefinido.
        """
        ok, frame = self.camera_dev.read()
        if ok:
            height, width = frame.shape[:2]
            self._ensure_texture(width, height)
        return ok, frame

    def _infer(self, frame) -> Tuple[List[Pose], float]:
        """Ejecuta inferencia de pose a través del caso de uso.

        Args:
            frame: Imagen BGR (numpy array) capturada por la cámara.

        Returns:
            Lista de `Pose` detectadas y confianza de la primera caja.
        """
        return self.usecase.pose_estimator.infer(frame)

    def _update_metrics(self, frame, poses, first_conf):
        """Actualiza métricas y aplica rig cuando hay una persona.

        Args:
            frame: Imagen BGR actual.
            poses: Lista de `Pose` detectadas.
            first_conf: Confianza (float) de la primera detección.

        Returns:
            Diccionario de métricas calculadas/actualizadas.
        """
        # ruta rápida si existe (evita inferir dos veces)
        if hasattr(self.usecase, "from_poses"):
            metrics = self.usecase.from_poses(poses, first_conf)
        else:
            metrics = self.usecase(frame)

        if poses:
            rig_metrics = self.rig.apply_pose(poses[0], first_conf)
            metrics.setdefault("angles", {}).update(
                rig_metrics.get("angles", {})
            )
            self.usecase.metrics_store.write(metrics)

        return metrics

    def _draw_hud_text(self, frame, metrics) -> None:
        """Dibuja texto de estado en el frame de cámara.

        Args:
            frame: Imagen BGR donde se sobrepone el texto.
            metrics: Diccionario con claves 'persons' y 'fps'.
        """
        txt = (
            f'{metrics.get("persons", 0)} persona(s) | '
            f'{metrics.get("fps", 0.0):.1f} FPS'
        )
        cv2.putText(
            frame,
            txt,
            (8, 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

    def _blit_to_texture(self, frame) -> None:
        """Copia el frame BGR → textura (RGB flip vertical).

        Args:
            frame: Imagen BGR a enviar a la textura del HUD.
        """
        rgb = np.flipud(frame)
        rgb = np.ascontiguousarray(rgb, dtype=np.uint8)
        self.tex.setRamImage(rgb)

    def cleanup(self) -> None:
        """Libera recursos externos.

        Args:
            None
        """
        try:
            self.camera_dev.release()
        except Exception:
            pass
