"""Talos: Sensor/Actuator abstraction layer for Project LOGOS."""

__version__ = "0.1.0"

from talos.sensors import Sensor, SimulatedCamera, SimulatedDepth, SimulatedIMU
from talos.actuators import Actuator, SimulatedMotor, SimulatedGripper
from talos.telemetry import TelemetryRecorder, TelemetryEvent, EventType

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
