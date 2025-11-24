"""Integration tests for multi-sensor suite coordination and data fusion."""

from typing import Tuple
import numpy as np
import pytest

from talos.sensors import SimulatedCamera, SimulatedDepth, SimulatedIMU


class SensorSuite:
    """Coordinated suite of multiple sensors."""

    def __init__(self) -> None:
        """Initialize sensor suite with camera, depth, and IMU."""
        self.camera = SimulatedCamera(name="camera", resolution=(640, 480))
        self.depth = SimulatedDepth(name="depth", resolution=(320, 240))
        self.imu = SimulatedIMU(name="imu")
        self._capture_count = 0

    def synchronized_capture(self) -> Tuple[np.ndarray, np.ndarray, Tuple]:
        """Capture data from all sensors simultaneously.

        Returns:
            Tuple of (rgb_image, depth_map, imu_data)
        """
        rgb = self.camera.read()
        depth = self.depth.read()
        imu = self.imu.read()
        self._capture_count += 1
        return rgb, depth, imu

    def enable_all(self) -> None:
        """Enable all sensors in the suite."""
        self.camera.enable()
        self.depth.enable()
        self.imu.enable()

    def disable_all(self) -> None:
        """Disable all sensors in the suite."""
        self.camera.disable()
        self.depth.disable()
        self.imu.disable()

    def get_suite_info(self) -> dict:
        """Get information about all sensors in the suite."""
        return {
            "camera": self.camera.get_info(),
            "depth": self.depth.get_info(),
            "imu": self.imu.get_info(),
            "capture_count": self._capture_count,
        }


@pytest.fixture
def sensor_suite() -> SensorSuite:
    """Provide a sensor suite for testing."""
    return SensorSuite()


def test_sensor_suite_initialization(sensor_suite: SensorSuite) -> None:
    """Test sensor suite initializes all sensors correctly."""
    assert sensor_suite.camera is not None
    assert sensor_suite.depth is not None
    assert sensor_suite.imu is not None
    assert sensor_suite.camera.is_enabled()
    assert sensor_suite.depth.is_enabled()
    assert sensor_suite.imu.is_enabled()


def test_synchronized_capture(sensor_suite: SensorSuite) -> None:
    """Test camera + depth sensor synchronized capture."""
    rgb, depth, imu = sensor_suite.synchronized_capture()

    # Verify camera data
    assert rgb.shape == (480, 640, 3)
    assert rgb.dtype == np.uint8

    # Verify depth data
    assert depth.shape == (240, 320)
    assert depth.dtype == np.float32

    # Verify IMU data
    acceleration, gyroscope = imu
    assert len(acceleration) == 3
    assert len(gyroscope) == 3


def test_timestamp_alignment(sensor_suite: SensorSuite) -> None:
    """Test IMU + camera timestamp alignment."""
    # Capture multiple times
    captures = []
    for _ in range(5):
        rgb, depth, imu = sensor_suite.synchronized_capture()
        info = sensor_suite.get_suite_info()
        captures.append(info)

    # Verify frame counts are aligned (all sensors captured same number of times)
    for i, capture_info in enumerate(captures):
        expected_count = i + 1
        # Camera and depth should have matching frame counts
        assert capture_info["camera"]["frame_count"] == expected_count
        assert capture_info["depth"]["frame_count"] == expected_count


def test_multi_sensor_data_fusion(sensor_suite: SensorSuite) -> None:
    """Test multi-sensor data fusion capabilities."""
    rgb, depth, imu = sensor_suite.synchronized_capture()

    # Verify data shapes are compatible for fusion
    # Camera is higher resolution than depth (typical configuration)
    assert rgb.shape[0] == 480 and rgb.shape[1] == 640
    assert depth.shape[0] == 240 and depth.shape[1] == 320

    # Calculate aspect ratios to ensure compatibility
    rgb_aspect = rgb.shape[1] / rgb.shape[0]
    depth_aspect = depth.shape[1] / depth.shape[0]
    assert abs(rgb_aspect - depth_aspect) < 0.01  # Same aspect ratio

    # Verify IMU provides motion data
    acceleration, gyroscope = imu
    assert isinstance(acceleration, np.ndarray)
    assert isinstance(gyroscope, np.ndarray)


def test_sensor_suite_enable_disable(sensor_suite: SensorSuite) -> None:
    """Test sensor suite initialization and enable/disable."""
    # All should be enabled by default
    assert sensor_suite.camera.is_enabled()
    assert sensor_suite.depth.is_enabled()
    assert sensor_suite.imu.is_enabled()

    # Disable all
    sensor_suite.disable_all()
    assert not sensor_suite.camera.is_enabled()
    assert not sensor_suite.depth.is_enabled()
    assert not sensor_suite.imu.is_enabled()

    # Enable all
    sensor_suite.enable_all()
    assert sensor_suite.camera.is_enabled()
    assert sensor_suite.depth.is_enabled()
    assert sensor_suite.imu.is_enabled()


def test_sensor_failure_handling(sensor_suite: SensorSuite) -> None:
    """Test sensor failure handling (one sensor fails)."""
    # Disable depth sensor to simulate failure
    sensor_suite.depth.disable()

    # Camera and IMU should still work
    rgb = sensor_suite.camera.read()
    imu = sensor_suite.imu.read()

    assert rgb.shape == (480, 640, 3)
    assert len(imu) == 2

    # Depth sensor should raise error
    with pytest.raises(RuntimeError, match="disabled"):
        sensor_suite.depth.read()


def test_sensor_recalibration(sensor_suite: SensorSuite) -> None:
    """Test sensor recalibration by resetting state."""
    # Capture some data
    for _ in range(5):
        sensor_suite.synchronized_capture()

    info_before = sensor_suite.get_suite_info()
    assert info_before["camera"]["frame_count"] == 5

    # Simulate recalibration by creating new sensors
    sensor_suite.camera = SimulatedCamera(name="camera", resolution=(640, 480))
    sensor_suite.depth = SimulatedDepth(name="depth", resolution=(320, 240))

    info_after = sensor_suite.get_suite_info()
    assert info_after["camera"]["frame_count"] == 0
    assert info_after["depth"]["frame_count"] == 0


def test_sensor_data_validation(sensor_suite: SensorSuite) -> None:
    """Test sensor data validation across suite."""
    rgb, depth, imu = sensor_suite.synchronized_capture()

    # Validate camera data
    assert rgb.min() >= 0
    assert rgb.max() <= 255
    assert not np.isnan(rgb).any()

    # Validate depth data
    assert depth.min() >= sensor_suite.depth.min_range - 0.5  # Allow for noise
    assert depth.max() <= sensor_suite.depth.max_range + 0.5
    assert not np.isnan(depth).any()
    assert not np.isinf(depth).any()

    # Validate IMU data
    acceleration, gyroscope = imu
    assert not np.isnan(acceleration).any()
    assert not np.isnan(gyroscope).any()
    # Check physical constraints
    assert np.linalg.norm(acceleration) <= 50.0  # Reasonable acceleration limit
    assert np.linalg.norm(gyroscope) <= 10.0  # Reasonable rotation rate


def test_sensor_suite_telemetry_aggregation(sensor_suite: SensorSuite) -> None:
    """Test sensor suite telemetry aggregation."""
    # Capture multiple times
    for _ in range(10):
        sensor_suite.synchronized_capture()

    info = sensor_suite.get_suite_info()

    # Verify telemetry
    assert info["capture_count"] == 10
    assert info["camera"]["frame_count"] == 10
    assert info["depth"]["frame_count"] == 10

    # All sensors should report enabled state
    assert info["camera"]["enabled"] is True
    assert info["depth"]["enabled"] is True
    assert info["imu"]["enabled"] is True


def test_sensor_suite_consistent_data_shape(sensor_suite: SensorSuite) -> None:
    """Test that sensors provide consistent data shapes across captures."""
    # Capture multiple times
    shapes = []
    for _ in range(5):
        rgb, depth, imu = sensor_suite.synchronized_capture()
        shapes.append(
            {
                "rgb": rgb.shape,
                "depth": depth.shape,
                "imu_accel": imu[0].shape,
                "imu_gyro": imu[1].shape,
            }
        )

    # All shapes should be identical
    first_shapes = shapes[0]
    for shape_set in shapes[1:]:
        assert shape_set == first_shapes


def test_sensor_suite_multiple_instances() -> None:
    """Test multiple sensor suite instances don't interfere."""
    suite1 = SensorSuite()
    suite2 = SensorSuite()

    # Capture from both
    rgb1, depth1, imu1 = suite1.synchronized_capture()
    rgb2, depth2, imu2 = suite2.synchronized_capture()

    # Both should work independently
    assert rgb1.shape == rgb2.shape
    assert depth1.shape == depth2.shape

    # Disable suite1
    suite1.disable_all()
    assert not suite1.camera.is_enabled()
    assert suite2.camera.is_enabled()  # suite2 should be unaffected


def test_sensor_suite_partial_failure_recovery() -> None:
    """Test recovery from partial sensor failures."""
    suite = SensorSuite()

    # Simulate camera failure
    suite.camera.disable()

    # Depth and IMU should still work
    depth = suite.depth.read()
    imu = suite.imu.read()

    assert depth.shape == (240, 320)
    assert len(imu) == 2

    # Recover camera
    suite.camera.enable()

    # Full capture should work again
    rgb, depth, imu = suite.synchronized_capture()
    assert rgb.shape == (480, 640, 3)
    assert depth.shape == (240, 320)
    assert len(imu) == 2


def test_sensor_suite_data_variability() -> None:
    """Test that sensor data varies appropriately across captures."""
    suite = SensorSuite()

    # Capture twice
    rgb1, depth1, imu1 = suite.synchronized_capture()
    rgb2, depth2, imu2 = suite.synchronized_capture()

    # RGB should vary (different frame patterns)
    assert not np.array_equal(rgb1, rgb2)

    # Depth should vary slightly (has time-based offset)
    assert not np.array_equal(depth1, depth2)

    # IMU should vary (has randomness)
    accel1, gyro1 = imu1
    accel2, gyro2 = imu2
    assert not np.array_equal(accel1, accel2)


def test_sensor_suite_performance() -> None:
    """Test sensor suite performance with multiple rapid captures."""
    suite = SensorSuite()

    # Perform many rapid captures
    captures = []
    for _ in range(100):
        rgb, depth, imu = suite.synchronized_capture()
        captures.append((rgb, depth, imu))

    # Verify all captures succeeded
    assert len(captures) == 100

    # Verify last capture has correct frame counts
    info = suite.get_suite_info()
    assert info["capture_count"] == 100
