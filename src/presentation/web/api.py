"""
Blueprint de API para inferencia de poses y consulta de métricas.

Endpoints:
- POST /infer   : recibe una imagen (archivo 'frame' o body en bytes) y devuelve
                  poses detectadas + métricas (inference_ms, server_fps, mean_kp_conf).
- GET  /metrics : devuelve un snapshot de las últimas métricas almacenadas.

Notas:
- Las imágenes deben venir codificadas (JPEG/PNG). Se decodifican con OpenCV.
- Las métricas se almacenan en un buffer circular en memoria.
"""

from __future__ import annotations

import time
from typing import Any

import cv2
import numpy as np
from flask import Blueprint, Response, current_app, jsonify, request

from ...application.services.metrics_service import MetricsService
from ...application.services.pose_service import PoseService
from ...domain.entities import Metrics
from ...domain.usecases.push_metrics import PushMetrics
from ...domain.usecases.run_inference import RunInference
from ...infrastructure.persistence.ring_buffer import RingBufferMetrics
from ...infrastructure.vision.yolo_pose_adapter import YOLOv8PoseAdapter

api_bp = Blueprint("api", __name__)


def build_containers() -> tuple[PoseService, MetricsService]:
    """
    Construye y cablea las dependencias de la capa de aplicación.

    Returns:
        tuple[PoseService, MetricsService]: Servicios listos para inyectar
        en la app Flask (por ejemplo, en create_app()).
    """
    model = YOLOv8PoseAdapter(weights="yolov8n-pose.pt", device="auto", imgsz=320)
    run_inf = RunInference(model)
    pose_service = PoseService(run_inf)

    rb = RingBufferMetrics(capacity=1800)
    push = PushMetrics(rb)
    metrics_service = MetricsService(push, rb)
    return pose_service, metrics_service


@api_bp.route("/infer", methods=["POST"])
def infer() -> Response:
    """
    Ejecuta la inferencia de pose sobre una imagen BGR.

    Args (Request):
        - Archivo 'frame' (multipart/form-data) con la imagen codificada (JPEG/PNG),
          o bien el body crudo (application/octet-stream) con los bytes de imagen.

    Returns:
        Response (application/json): Objeto con:
            - poses: lista de poses [{bbox, score, keypoints[[x,y,c], ...]}, ...]
            - inference_ms: tiempo de inferencia en milisegundos (float)
            - server_fps: FPS promedio (EMA) del servidor (float)
            - mean_kp_conf: confianza media de keypoints (float)
    """
    pose_service: PoseService = current_app.config["POSE_SERVICE"]
    metrics_service: MetricsService = current_app.config["METRICS_SERVICE"]

    # --- Leer bytes de imagen desde 'frame' o desde el body ---
    file = request.files.get("frame")
    if file is None:
        data = request.get_data()
        if not data:
            return jsonify({"error": "no image"}), 400
        arr = np.frombuffer(data, dtype=np.uint8)
    else:
        arr = np.frombuffer(file.read(), dtype=np.uint8)

    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return jsonify({"error": "bad image"}), 400

    # --- Inferencia ---
    result = pose_service.infer_from_bgr(img)

    # --- mean keypoint confidence ---
    confs = [kp.c for p in result.poses for kp in p.keypoints]
    mean_kp_conf = float(np.mean(confs)) if confs else 0.0

    # --- Push métricas ---
    m = Metrics(
        t=time.time(),
        inference_ms=result.inference_ms,
        server_fps=result.server_fps,
        mean_kp_conf=mean_kp_conf,
    )
    metrics_service.push(m)

    # --- Serialización de poses ---
    poses_json: list[dict[str, Any]] = [
        {
            "bbox": list(p.bbox),
            "score": p.score,
            "keypoints": [[kp.x, kp.y, kp.c] for kp in p.keypoints],
        }
        for p in result.poses
    ]

    return jsonify(
        {
            "poses": poses_json,
            "inference_ms": result.inference_ms,
            "server_fps": result.server_fps,
            "mean_kp_conf": mean_kp_conf,
        }
    )


@api_bp.route("/metrics", methods=["GET"])
def metrics() -> Response:
    """
    Devuelve un snapshot de las últimas métricas.

    Query Args:
        n (int, opcional): Número de elementos del snapshot (por defecto 120).

    Returns:
        Response (application/json): Lista de dicts con métricas.
    """
    metrics_service: MetricsService = current_app.config["METRICS_SERVICE"]
    n = request.args.get("n", default=120, type=int)
    return jsonify(metrics_service.snapshot(n))
