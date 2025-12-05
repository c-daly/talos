"""Tests for simulated depth sensor."""

import pytest
import numpy as np
from talos.sensors.depth import SimulatedDepth


def test_depth_initialization() -> None:
    """Test depth sensor initialization."""
    depth = SimulatedDepth(
        name="test_depth", resolution=(320, 240), min_range=0.5, max_range=5.0
    )
    assert depth.name == "test_depth"
    assert depth.resolution == (320, 240)
    assert depth.min_range == 0.5
    assert depth.max_range == 5.0


def test_depth_read() -> None:
    """Test depth sensor read functionality."""
    depth = SimulatedDepth(resolution=(160, 120), min_range=0.5, max_range=5.0)
    depth_map = depth.read()

    # Check shape: (height, width)
    assert depth_map.shape == (120, 160)
    assert depth_map.dtype == np.float32

    # Check values are mostly in valid range (allowing for noise)
    assert np.mean(depth_map) >= 0.3  # Some margin below min_range due to noise
    assert np.mean(depth_map) <= 5.2  # Some margin above max_range due to noise


def test_depth_disabled_read() -> None:
    """Test that disabled depth sensor raises error."""
    depth = SimulatedDepth()
    depth.disable()

    with pytest.raises(RuntimeError, match="disabled"):
        depth.read()


def test_depth_frame_count() -> None:
    """Test frame count increments."""
    depth = SimulatedDepth()

    assert depth.get_info()["frame_count"] == 0
    depth.read()
    assert depth.get_info()["frame_count"] == 1


def test_depth_varying_output() -> None:
    """Test that depth output varies over time."""
    depth = SimulatedDepth(resolution=(80, 60))

    depth_map1 = depth.read()
    depth_map2 = depth.read()

    # Depth maps should be slightly different
    assert not np.array_equal(depth_map1, depth_map2)
