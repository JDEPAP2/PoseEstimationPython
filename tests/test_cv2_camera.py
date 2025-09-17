import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath("src"))

from src.infrastructure.video.camera_cv2 import Cv2Camera


@patch("src.infrastructure.video.camera_cv2.cv2.VideoCapture")
def test_open_success(mock_videocap: MagicMock) -> None:
    """
    Debe abrir la cámara exitosamente si VideoCapture.isOpened() devuelve True.

    Args:
        mock_videocap (MagicMock): Mock de cv2.VideoCapture.
    """
    mock_cap: MagicMock = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_videocap.return_value = mock_cap

    camera: Cv2Camera = Cv2Camera(cam_index=1)
    camera.open()

    mock_videocap.assert_called_once_with(1)
    assert camera.cap == mock_cap


@patch("src.infrastructure.video.camera_cv2.cv2.VideoCapture")
def test_read_returns_frame(mock_videocap: MagicMock) -> None:
    """
    Debe devolver (ok, frame) al llamar a read().

    Args:
        mock_videocap (MagicMock): Mock de cv2.VideoCapture.
    """
    mock_cap: MagicMock = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (True, "fake_frame")
    mock_videocap.return_value = mock_cap

    camera: Cv2Camera = Cv2Camera()
    camera.open()
    ok, frame = camera.read()

    assert ok is True
    assert frame == "fake_frame"
    mock_cap.read.assert_called_once()
