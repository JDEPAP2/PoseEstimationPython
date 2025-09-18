"""Lanzador principal del pipeline de pose + visualización + dashboard.

- Inicia la cámara y el estimador de pose (Ultralytics YOLOv8).
- Crea una vista Panda3D que consume frames y actualiza métricas.
- Lanza el dashboard de Streamlit en un proceso separado.
"""

from __future__ import annotations

import atexit
import os
import subprocess
import sys

# --- Rutas base del proyecto -------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
MODELS_DIR = os.path.join(ASSETS_DIR, "models")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
DASH_DIR = os.path.join(OUTPUTS_DIR, "dashboards")
WEIGHTS_DIR = os.path.join(OUTPUTS_DIR, "yolo", "weights")

os.makedirs(WEIGHTS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(DASH_DIR, exist_ok=True)

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# --- Importaciones locales (tras ajustar sys.path) ---------------------------

from infrastructure.video.camera_cv2 import Cv2Camera
from infrastructure.pose.yolov8_ultralytics import YoloV8PoseEstimator
from infrastructure.rig.panda3d_app import Panda3DView
from infrastructure.dashboard.json_store import JsonMetricsStore
from application.usecases import ProcessFrameUseCase


def main(
    glb_path: str,
    cam_index: int = 0,
    imgsz: int = 640,
    port: int = 8501,
) -> None:
    """Punto de entrada del pipeline.

    Args:
        glb_path: Ruta al modelo .glb del rig.
        cam_index: Índice de la cámara (OpenCV).
        imgsz: Tamaño de entrada para YOLOv8.
        port: Puerto del dashboard de Streamlit (informativo).
    """
    metrics_json = os.path.join(DASH_DIR, "pose_metrics.json")

    camera = Cv2Camera(cam_index=cam_index)
    pose_estimator = YoloV8PoseEstimator(
        imgsz=imgsz,
        save_outputs=False,
        out_dir=os.path.join(OUTPUTS_DIR, "yolo"),
        weights_dir=WEIGHTS_DIR,
        weights_name="yolov8n-pose.pt",
    )
    store = JsonMetricsStore(json_path=metrics_json)

    usecase = ProcessFrameUseCase(
        pose_estimator=pose_estimator,
        metrics_store=store,
    )

    app = Panda3DView(glb_path=glb_path, camera=camera, usecase=usecase)

    # Lanzar Streamlit en un proceso aparte
    dash = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "./src/presentation/dashboard/app.py",
        ]
    )

    # Registrar limpieza ordenada al salir
    atexit.register(app.cleanup)
    atexit.register(dash.terminate)

    # Bloqueante: corre el loop de Panda3D
    app.run()


def _parse_args(argv: list[str]) -> tuple[str, int, int, int]:
    """Parsea argumentos de línea de comandos.

    Formato:
        python main.py assets/models/model.glb [cam_index] [imgsz] [port]

    Returns:
        Tupla (glb_path, cam_index, imgsz, port).
    """
    if len(argv) < 2:
        print(
            "Uso: python main.py assets/models/model.glb [cam_index] [imgsz] [port]"
        )
        sys.exit(0)

    glb_path = argv[1]
    cam_index = int(argv[2]) if len(argv) > 2 else 0
    imgsz = int(argv[3]) if len(argv) > 3 else 640
    port = int(argv[4]) if len(argv) > 4 else 8501
    return glb_path, cam_index, imgsz, port


if __name__ == "__main__":
    glb_arg, cam_arg, sz_arg, port_arg = _parse_args(sys.argv)
    main(glb_arg, cam_arg, sz_arg, port_arg)
