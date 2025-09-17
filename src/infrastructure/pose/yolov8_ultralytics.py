"""Adaptador de Ultralytics YOLOv8 para estimación de poses humanas."""

from __future__ import annotations

import os
import shutil
from typing import List, Optional, Tuple

import numpy as np
from ultralytics import YOLO

from domain.entities import Keypoint, Pose
from domain.ports import PoseEstimator

YOLO_URLS = {
    "yolov8n-pose.pt": (
        "https://github.com/ultralytics/assets/releases/"
        "download/v8.3.0/yolov8n-pose.pt"
    )
}


class YoloV8PoseEstimator(PoseEstimator):
    """Estimador de poses usando YOLOv8 de Ultralytics."""

    def __init__(
        self,
        weights_name: str = "yolov8n-pose.pt",
        imgsz: int = 640,
        save_outputs: bool = False,
        out_dir: Optional[str] = None,
        weights_dir: Optional[str] = None,
    ) -> None:
        """Inicializa el estimador con manejo de pesos automático.

        Args:
            weights_name: Nombre del archivo de pesos YOLOv8.
            imgsz: Tamaño de entrada para la red.
            save_outputs: Si True, guarda salidas (no usado aquí).
            out_dir: Carpeta de outputs (para guardados opcionales).
            weights_dir: Carpeta destino donde se almacenarán los pesos.
        """
        self.imgsz = imgsz
        self.save = bool(save_outputs)
        self.project = out_dir if out_dir else None

        # Resolver ruta destino de los pesos
        self.weights_dir = weights_dir or os.getcwd()
        os.makedirs(self.weights_dir, exist_ok=True)
        self.weights_path = os.path.join(self.weights_dir, weights_name)

        # 1) Ya existe en destino
        if os.path.exists(self.weights_path):
            self.model = YOLO(self.weights_path)
            return

        # 2) Existe en CWD → mover/copiar a destino
        cwd_path = os.path.join(os.getcwd(), weights_name)
        if os.path.exists(cwd_path):
            try:
                shutil.move(cwd_path, self.weights_path)
            except Exception:
                shutil.copy2(cwd_path, self.weights_path)
                try:
                    os.remove(cwd_path)
                except Exception:
                    pass
            self.model = YOLO(self.weights_path)
            return

        # 3) No existe → YOLO lo descargará (o fallback manual)
        try:
            self.model = YOLO(self.weights_path)
        except Exception:
            import urllib.request

            url = YOLO_URLS.get(weights_name)
            if url:
                urllib.request.urlretrieve(url, self.weights_path)
                self.model = YOLO(self.weights_path)
            else:
                # Último recurso: usar el nombre pelado
                self.model = YOLO(weights_name)

    def infer(
        self,
        frame_bgr: np.ndarray,
    ) -> Tuple[List[Pose], Optional[float]]:
        """Ejecuta inferencia sobre un frame BGR.

        Args:
            frame_bgr: Imagen en formato BGR (numpy array).

        Returns:
            Una tupla con:
              - Lista de `Pose` detectadas.
              - Confianza (float) de la primera detección, si existe.
        """
        results = self.model(
            frame_bgr,
            imgsz=self.imgsz,
            verbose=False,
            save=False,
        )
        res = results[0]

        poses: List[Pose] = []
        first_conf: Optional[float] = None

        if res.keypoints is not None:
            kps = res.keypoints.data.cpu().numpy()  # [N, 17, 3]
            if (
                res.boxes is not None
                and res.boxes.conf is not None
                and len(res.boxes.conf) > 0
            ):
                first_conf = float(res.boxes.conf.cpu().numpy()[0])
            for person in kps:
                pose_kps = [
                    Keypoint(float(x), float(y), float(c))
                    for (x, y, c) in person
                ]
                poses.append(Pose(keypoints=pose_kps))

        return poses, first_conf
