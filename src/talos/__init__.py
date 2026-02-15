"""Talos: Sensor/Actuator abstraction layer for Project LOGOS."""

__version__ = "0.1.0"

from talos.sensors import Sensor, SimulatedCamera, SimulatedDepth, SimulatedIMU
from talos.actuators import Actuator, SimulatedMotor, SimulatedGripper
from talos.telemetry import TelemetryRecorder, TelemetryEvent, EventType

# Initialise structured logging for the talos namespace.
# Consumer services can reconfigure by calling setup_logging() again.
try:
    from logos_test_utils.logging import setup_logging

    setup_logging("talos")
except ImportError:  # pragma: no cover
    pass

# Fixtures are imported separately to avoid pytest import issues
# when talos is used outside of testing context
try:
    from talos.fixtures import (
        mock_camera,
        mock_depth_sensor,
        mock_imu,
        mock_motor,
        mock_gripper,
        mock_telemetry,
        mock_pick_and_place,
        mock_robot_arm,
        mock_sensor_suite,
    )

    __all__ = [
        "Sensor",
        "SimulatedCamera",
        "SimulatedDepth",
        "SimulatedIMU",
        "Actuator",
        "SimulatedMotor",
        "SimulatedGripper",
        "TelemetryRecorder",
        "TelemetryEvent",
        "EventType",
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
except ImportError:  # pragma: no cover
    # pytest not available, fixtures not imported
    __all__ = [
        "Sensor",
        "SimulatedCamera",
        "SimulatedDepth",
        "SimulatedIMU",
        "Actuator",
        "SimulatedMotor",
        "SimulatedGripper",
        "TelemetryRecorder",
        "TelemetryEvent",
        "EventType",
    ]
