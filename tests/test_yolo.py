import os
import sys
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from typing import Any, Tuple

sys.path.append(os.path.abspath("src"))

from src.infrastructure.pose.yolov8_ultralytics import YoloV8PoseEstimator
from domain.entities import Pose, Keypoint


@patch("src.infrastructure.pose.yolov8_ultralytics.YOLO")
def test_init_with_existing_weights(mock_yolo: MagicMock, tmp_path: Any) -> None:
    """
    Debe cargar el modelo si el archivo de pesos ya existe en el directorio destino.

    Args:
        mock_yolo (MagicMock): Mock de la clase YOLO de ultralytics.
        tmp_path (Any): Carpeta temporal generada por pytest.
    """
    weights_path = tmp_path / "yolov8n-pose.pt"
    weights_path.write_text("dummy")

    estimator: YoloV8PoseEstimator = YoloV8PoseEstimator(weights_dir=str(tmp_path))

    mock_yolo.assert_called_once_with(str(weights_path))
    assert os.path.exists(estimator.weights_path)


@patch("src.infrastructure.pose.yolov8_ultralytics.YOLO")
def test_infer_with_keypoints_and_conf(mock_yolo: MagicMock) -> None:
    """
    Debe devolver Poses y la primera confianza cuando hay keypoints y boxes.

    Args:
        mock_yolo (MagicMock): Mock de la clase YOLO de ultralytics.
    """
    mock_result: MagicMock = MagicMock()
    mock_result.keypoints.data.cpu().numpy.return_value = np.array(
        [[[10, 20, 0.9], [30, 40, 0.8]]]
    )

    mock_conf: MagicMock = MagicMock()
    mock_conf.__len__.return_value = 1
    mock_conf.cpu().numpy.return_value = np.array([0.85])

    mock_boxes: MagicMock = MagicMock()
    mock_boxes.conf = mock_conf
    mock_result.boxes = mock_boxes

    mock_yolo_instance: MagicMock = MagicMock()
    mock_yolo_instance.return_value = [mock_result]
    mock_yolo.return_value = mock_yolo_instance

    estimator: YoloV8PoseEstimator = YoloV8PoseEstimator(weights_dir=os.getcwd())
    frame: np.ndarray = np.zeros((480, 640, 3), dtype=np.uint8)

    poses, conf = estimator.infer(frame)

    assert isinstance(poses[0], Pose)
    assert isinstance(poses[0].keypoints[0], Keypoint)
    assert conf == pytest.approx(0.85)


@patch("src.infrastructure.pose.yolov8_ultralytics.YOLO")
def test_infer_with_no_keypoints(mock_yolo: MagicMock) -> None:
    """
    Debe devolver lista vacía y None cuando no hay keypoints.

    Args:
        mock_yolo (MagicMock): Mock de la clase YOLO de ultralytics.
    """
    mock_result: MagicMock = MagicMock()
    mock_result.keypoints = None
    mock_result.boxes = None

    mock_yolo_instance: MagicMock = MagicMock()
    mock_yolo_instance.return_value = [mock_result]
    mock_yolo.return_value = mock_yolo_instance

    estimator: YoloV8PoseEstimator = YoloV8PoseEstimator(weights_dir=os.getcwd())
    frame: np.ndarray = np.zeros((480, 640, 3), dtype=np.uint8)

    poses, conf = estimator.infer(frame)

    assert poses == []
    assert conf is None
