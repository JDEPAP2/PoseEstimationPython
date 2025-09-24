"""
Adaptador de modelo de pose basado en Ultralytics YOLOv8.

- Resuelve y materializa los pesos (nombre .pt o ruta).
- Selecciona dispositivo automáticamente (cuda/mps/cpu).
- Expone `infer(bgr_image)` que devuelve `InferenceResult`.

Prioridad de dispositivo:
1) valor explícito en `device`
2) auto: cuda > mps > cpu
"""

from __future__ import annotations

import os
import time
import shutil
from pathlib import Path
from typing import Optional

import numpy as np
import torch
from ultralytics import YOLO

from ...domain.entities import InferenceResult, Pose, Keypoint
from ...domain.repositories import PoseModel


class YOLOv8PoseAdapter(PoseModel):
    """
    Adaptador de YOLOv8-pose para la interfaz `PoseModel`.

    Args:
        weights (str): Ruta o nombre de archivo de pesos (.pt), p. ej. "yolov8n-pose.pt".
        device (str): "auto", "cuda", "mps" o "cpu".
        imgsz (int): Tamaño de entrada del modelo (lado más corto).

    Attributes:
        _imgsz (int): Tamaño de entrada.
        _device (str): Dispositivo seleccionado.
        _models_dir (Path): Carpeta local para pesos materializados.
        _model (YOLO): Modelo Ultralytics cargado.
    """

    def __init__(
        self,
        weights: str = "yolov8n-pose.pt",
        device: str = "auto",
        imgsz: int = 320,
    ) -> None:
        self._imgsz: int = imgsz
        self._device: str = self._resolve_device(device)
        self._models_dir: Path = self._ensure_models_dir()

        local_weights: Path = self._resolve_and_materialize_weights(
            weights, self._models_dir
        )

        self._model = YOLO(str(local_weights))
        # Enviar a dispositivo (compatibilidad con distintas versiones de Ultralytics)
        try:
            if hasattr(self._model, "to"):
                self._model.to(self._device)
            elif hasattr(self._model, "model"):
                self._model.model.to(self._device)
        except Exception:
            # No interrumpir si la versión cambió; continuar en CPU si falla.
            pass

        # Half precision en CUDA (si procede)
        try:
            if self._device == "cuda" and hasattr(self._model, "model"):
                self._model.model.half()
        except Exception:
            pass

    # ---------- Helpers ----------

    def _resolve_device(self, device: str) -> str:
        """
        Selecciona el dispositivo de cómputo.

        Args:
            device (str): "auto", "cuda", "mps" o "cpu".

        Returns:
            str: Dispositivo efectivo.
        """
        if device != "auto":
            return device
        if torch.cuda.is_available():
            torch.backends.cudnn.benchmark = True
            return "cuda"
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    def _ensure_models_dir(self) -> Path:
        """
        Crea (si no existe) la carpeta local de modelos.

        Returns:
            Path: Ruta absoluta a outputs/models.
        """
        p = Path("outputs") / "models"
        p.mkdir(parents=True, exist_ok=True)
        return p.resolve()

    def _looks_like_filename(self, s: str) -> bool:
        """
        Verifica si `s` parece un nombre de archivo .pt (sin ruta).

        Args:
            s (str): Cadena a evaluar.

        Returns:
            bool: True si termina en .pt y no incluye separadores de ruta.
        """
        return s.endswith(".pt") and (os.sep not in s) and ("/" not in s)

    def _search_in_ultralytics_cache(self, filename: str) -> Optional[Path]:
        """
        Busca un archivo en directorios típicos de caché de Ultralytics.

        Args:
            filename (str): Nombre de archivo (.pt).

        Returns:
            Optional[Path]: Ruta encontrada o None.
        """
        home = Path.home()
        candidates = [
            home / ".cache" / "Ultralytics",
            home / ".config" / "Ultralytics",
            home / ".ultralytics",
        ]
        for root in candidates:
            if not root.exists():
                continue
            try:
                found = list(root.rglob(filename))
                if found:
                    found.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                    return found[0]
            except Exception:
                continue
        return None

    def _force_download_via_ultralytics(self, weights_name: str) -> Optional[Path]:
        """
        Fuerza la descarga de pesos a través del cargador de Ultralytics si no existen.

        Args:
            weights_name (str): Nombre del archivo de pesos.

        Returns:
            Optional[Path]: Ruta en caché si se descargó con éxito, None si falló.
        """
        try:
            _ = YOLO(weights_name)  # dispara descarga si no existe localmente
        except Exception:
            return None
        return self._search_in_ultralytics_cache(weights_name)

    def _resolve_and_materialize_weights(self, weights: str, models_dir: Path) -> Path:
        """
        Resuelve y materializa los pesos localmente en `models_dir`.

        Casos:
            A) `weights` es ruta existente → se usa tal cual (si está en raíz, se mueve).
            B) `weights` es nombre .pt → se busca en caché; si no, se descarga y copia.
            C) Cualquier otro string → se devuelve su `Path.resolve()` (puede fallar luego).

        Args:
            weights (str): Ruta o nombre de archivo .pt.
            models_dir (Path): Carpeta local destino.

        Returns:
            Path: Ruta absoluta de los pesos a usar.
        """
        wpath = Path(weights)

        # Caso A: ruta existente
        if wpath.exists():
            try:
                # Si está en el cwd (archivo suelto), muévelo a outputs/models
                if wpath.parent.resolve() == Path(".").resolve():
                    target = (models_dir / wpath.name).resolve()
                    shutil.move(str(wpath), str(target))
                    return target
            except Exception:
                # Si falla la comparación o el move, úsalo como está.
                return wpath.resolve()
            return wpath.resolve()

        # Caso B: nombre de archivo .pt
        if self._looks_like_filename(weights):
            local_target = (models_dir / weights).resolve()
            if local_target.exists():
                return local_target

            cached = self._search_in_ultralytics_cache(weights)
            if cached and cached.exists():
                shutil.copy2(str(cached), str(local_target))
                # Limpieza de descargas en raíz si existieran
                root_file = Path(weights)
                if root_file.exists():
                    root_file.unlink()
                return local_target

            downloaded = self._force_download_via_ultralytics(weights)
            if downloaded and downloaded.exists():
                shutil.copy2(str(downloaded), str(local_target))
                root_file = Path(weights)
                if root_file.exists():
                    root_file.unlink()
                return local_target

            # Último recurso: devolver el target (Ultralytics puede resolverlo al cargar)
            return local_target

        # Caso C: algo que no parece archivo .pt → devolver ruta resuelta (puede no existir)
        return wpath.resolve()

    # ---------- Inferencia ----------

    def infer(self, bgr_image: np.ndarray) -> InferenceResult:
        """
        Ejecuta la inferencia de pose sobre una imagen en formato BGR.

        Args:
            bgr_image (np.ndarray): Imagen BGR (por ejemplo, salida de OpenCV).

        Returns:
            InferenceResult: Poses detectadas, tiempo de inferencia (ms) y fps=0.0
                (el fps de servidor se calcula aguas arriba).
        """
        t0 = time.time()

        # Ultralytics espera RGB
        rgb = bgr_image[:, :, ::-1]

        out = self._model.predict(
            source=rgb,
            verbose=False,
            device=self._device,
            imgsz=self._imgsz,
            max_det=1,
            conf=0.25,
            iou=0.5,
            half=(self._device == "cuda"),
        )

        dt_ms = (time.time() - t0) * 1000.0
        poses: list[Pose] = []

        for r in out:
            if getattr(r, "keypoints", None) is None:
                continue

            kxy = r.keypoints.xy.cpu().numpy()
            if getattr(r.keypoints, "conf", None) is not None:
                kcf = r.keypoints.conf.cpu().numpy()
            else:
                kcf = np.ones(kxy.shape[:2], dtype=np.float32)

            for i in range(kxy.shape[0]):
                kpts = [
                    Keypoint(
                        float(kxy[i, j, 0]),
                        float(kxy[i, j, 1]),
                        float(kcf[i, j]),
                    )
                    for j in range(kxy.shape[1])
                ]

                if getattr(r, "boxes", None) is not None and len(r.boxes) > i:
                    b = r.boxes[i].xywh.cpu().numpy()[0]
                    bbox = (float(b[0]), float(b[1]), float(b[2]), float(b[3]))
                    score = float(r.boxes[i].conf.cpu().numpy()[0])
                else:
                    bbox = (0.0, 0.0, 0.0, 0.0)
                    score = 0.0

                poses.append(Pose(kpts, bbox, score))

        return InferenceResult(poses=poses, inference_ms=dt_ms, server_fps=0.0)
