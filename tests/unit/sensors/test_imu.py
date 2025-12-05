"""Tests for simulated IMU sensor."""

import pytest
import numpy as np
from talos.sensors.imu import SimulatedIMU


def test_imu_initialization() -> None:
    """Test IMU initialization."""
    imu = SimulatedIMU(name="test_imu")
    assert imu.name == "test_imu"


def test_imu_read() -> None:
    """Test IMU read functionality."""
    imu = SimulatedIMU()
    acceleration, gyroscope = imu.read()

    # Check shapes
    assert acceleration.shape == (3,)
    assert gyroscope.shape == (3,)
    assert acceleration.dtype == np.float32
    assert gyroscope.dtype == np.float32

    # Acceleration should be close to gravity (-9.81 in z)
    assert -11.0 < acceleration[2] < -8.0  # Allowing for noise


def test_imu_disabled_read() -> None:
    """Test that disabled IMU raises error."""
    imu = SimulatedIMU()
    imu.disable()

    with pytest.raises(RuntimeError, match="disabled"):
        imu.read()


def test_imu_sample_count() -> None:
    """Test sample count increments."""
    imu = SimulatedIMU()

    assert imu.get_info()["sample_count"] == 0
    imu.read()
    assert imu.get_info()["sample_count"] == 1
    imu.read()
    assert imu.get_info()["sample_count"] == 2


def test_imu_varying_output() -> None:
    """Test that IMU output varies over time."""
    imu = SimulatedIMU()

    accel1, gyro1 = imu.read()
    accel2, gyro2 = imu.read()

    # Values should vary (but not by much for acceleration)
    assert not np.array_equal(accel1, accel2)
    assert not np.array_equal(gyro1, gyro2)
