"""Sensor module for Talos."""

from talos.sensors.base import Sensor
from talos.sensors.camera import SimulatedCamera
from talos.sensors.depth import SimulatedDepth
from talos.sensors.imu import SimulatedIMU

__all__ = ["Sensor", "SimulatedCamera", "SimulatedDepth", "SimulatedIMU"]
