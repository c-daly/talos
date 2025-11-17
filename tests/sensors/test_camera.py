"""Tests for simulated camera sensor."""

import pytest
import numpy as np
from talos.sensors.camera import SimulatedCamera


def test_camera_initialization() -> None:
    """Test camera initialization."""
    camera = SimulatedCamera(name="test_camera", resolution=(640, 480))
    assert camera.name == "test_camera"
    assert camera.resolution == (640, 480)


def test_camera_read() -> None:
    """Test camera read functionality."""
    camera = SimulatedCamera(resolution=(320, 240))
    image = camera.read()

    # Check shape: (height, width, 3)
    assert image.shape == (240, 320, 3)
    assert image.dtype == np.uint8

    # Check values are in valid range
    assert np.all(image >= 0)
    assert np.all(image <= 255)


def test_camera_disabled_read() -> None:
    """Test that disabled camera raises error."""
    camera = SimulatedCamera()
    camera.disable()

    with pytest.raises(RuntimeError, match="disabled"):
        camera.read()


def test_camera_frame_count() -> None:
    """Test frame count increments."""
    camera = SimulatedCamera()

    assert camera.get_info()["frame_count"] == 0
    camera.read()
    assert camera.get_info()["frame_count"] == 1
    camera.read()
    assert camera.get_info()["frame_count"] == 2


def test_camera_varying_output() -> None:
    """Test that camera output varies over time."""
    camera = SimulatedCamera(resolution=(100, 100))

    image1 = camera.read()
    image2 = camera.read()

    # Images should be different
    assert not np.array_equal(image1, image2)
