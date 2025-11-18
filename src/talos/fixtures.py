"""Pytest fixtures for mock hardware testing.

This module provides reusable pytest fixtures for testing with simulated
hardware components. These fixtures are designed to be consumed by Sophia's
test harness and other testing frameworks.
"""

from typing import Generator
import pytest
from talos.sensors import SimulatedCamera, SimulatedDepth, SimulatedIMU
from talos.actuators import SimulatedMotor, SimulatedGripper
from talos.scenarios import PickAndPlaceScenario
from talos.telemetry import TelemetryRecorder


@pytest.fixture
def mock_camera() -> Generator[SimulatedCamera, None, None]:
    """Provide a simulated camera sensor.

    Yields:
        SimulatedCamera instance with default configuration

    Example:
        def test_camera_reading(mock_camera):
            image = mock_camera.read()
            assert image is not None
    """
    camera = SimulatedCamera(name="test_camera", resolution=(640, 480))
    yield camera
    # Cleanup if needed
    camera.disable()


@pytest.fixture
def mock_depth_sensor() -> Generator[SimulatedDepth, None, None]:
    """Provide a simulated depth sensor.

    Yields:
        SimulatedDepth instance with default configuration

    Example:
        def test_depth_reading(mock_depth_sensor):
            depth_map = mock_depth_sensor.read()
            assert depth_map is not None
    """
    depth = SimulatedDepth(name="test_depth", resolution=(320, 240))
    yield depth
    depth.disable()


@pytest.fixture
def mock_imu() -> Generator[SimulatedIMU, None, None]:
    """Provide a simulated IMU (Inertial Measurement Unit).

    Yields:
        SimulatedIMU instance with default configuration

    Example:
        def test_imu_reading(mock_imu):
            accel, gyro = mock_imu.read()
            assert accel is not None
            assert gyro is not None
    """
    imu = SimulatedIMU(name="test_imu")
    yield imu
    imu.disable()


@pytest.fixture
def mock_motor() -> Generator[SimulatedMotor, None, None]:
    """Provide a simulated motor actuator.

    Yields:
        SimulatedMotor instance with default configuration

    Example:
        def test_motor_control(mock_motor):
            mock_motor.set_position(1.57)
            assert mock_motor.get_position() == 1.57
    """
    motor = SimulatedMotor(name="test_motor", min_position=-3.14, max_position=3.14)
    yield motor
    motor.disable()


@pytest.fixture
def mock_gripper() -> Generator[SimulatedGripper, None, None]:
    """Provide a simulated gripper actuator.

    Yields:
        SimulatedGripper instance with default configuration

    Example:
        def test_gripper_control(mock_gripper):
            mock_gripper.close()
            assert mock_gripper.get_state()["is_closed"]
    """
    gripper = SimulatedGripper(name="test_gripper")
    yield gripper
    gripper.disable()


@pytest.fixture
def mock_telemetry() -> Generator[TelemetryRecorder, None, None]:
    """Provide a telemetry recorder for tracking operations.

    Yields:
        TelemetryRecorder instance with default configuration

    Example:
        def test_telemetry_tracking(mock_telemetry, mock_motor):
            motor = SimulatedMotor(name="motor", telemetry=mock_telemetry)
            motor.set_position(1.0)
            events = mock_telemetry.get_events()
            assert len(events) > 0
    """
    telemetry = TelemetryRecorder(max_events=1000)
    yield telemetry
    telemetry.clear()


@pytest.fixture
def mock_pick_and_place() -> Generator[PickAndPlaceScenario, None, None]:
    """Provide a complete pick-and-place scenario with all hardware.

    This fixture provides a fully configured pick-and-place scenario with:
    - Simulated sensors (camera, depth, IMU)
    - Simulated actuators (3 motors + gripper)
    - Telemetry tracking
    - Pre-configured objects and locations

    Yields:
        PickAndPlaceScenario instance ready for testing

    Example:
        def test_pick_and_place(mock_pick_and_place):
            scenario = mock_pick_and_place
            success, actions = scenario.execute_pick_and_place("cup", "shelf")
            assert success
            assert len(actions) == 4
    """
    scenario = PickAndPlaceScenario()
    yield scenario
    # Reset to clean state after test
    scenario.reset()


@pytest.fixture
def mock_robot_arm() -> Generator[dict, None, None]:
    """Provide a simulated robot arm with multiple joints.

    This fixture creates a dictionary of motors representing a 3-joint robot arm,
    suitable for testing multi-axis motion and coordination.

    Yields:
        Dictionary containing motor instances for each joint

    Example:
        def test_robot_arm_coordination(mock_robot_arm):
            arm = mock_robot_arm
            arm["joint1"].set_position(0.5)
            arm["joint2"].set_position(1.0)
            arm["joint3"].set_position(1.5)
            assert all(m.get_position() > 0 for m in arm.values())
    """
    arm = {
        "joint1": SimulatedMotor(name="joint1", min_position=-1.57, max_position=1.57),
        "joint2": SimulatedMotor(name="joint2", min_position=-1.57, max_position=1.57),
        "joint3": SimulatedMotor(name="joint3", min_position=-1.57, max_position=1.57),
    }
    yield arm
    # Cleanup
    for motor in arm.values():
        motor.disable()


@pytest.fixture
def mock_sensor_suite() -> Generator[dict, None, None]:
    """Provide a complete suite of sensors.

    This fixture creates a dictionary of all available sensor types,
    useful for testing sensor fusion and multi-modal perception.

    Yields:
        Dictionary containing all sensor instances

    Example:
        def test_sensor_suite(mock_sensor_suite):
            sensors = mock_sensor_suite
            image = sensors["camera"].read()
            depth = sensors["depth"].read()
            accel, gyro = sensors["imu"].read()
            assert image is not None
            assert depth is not None
    """
    sensors = {
        "camera": SimulatedCamera(name="suite_camera", resolution=(640, 480)),
        "depth": SimulatedDepth(name="suite_depth", resolution=(320, 240)),
        "imu": SimulatedIMU(name="suite_imu"),
    }
    yield sensors
    # Cleanup
    for sensor in sensors.values():
        sensor.disable()


# Export all fixtures for easy import
__all__ = [
    "mock_camera",
    "mock_depth_sensor",
    "mock_imu",
    "mock_motor",
    "mock_gripper",
    "mock_telemetry",
    "mock_pick_and_place",
    "mock_robot_arm",
    "mock_sensor_suite",
]
