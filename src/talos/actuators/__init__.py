"""Actuator module for Talos."""

from talos.actuators.base import Actuator
from talos.actuators.motor import SimulatedMotor
from talos.actuators.gripper import SimulatedGripper

__all__ = ["Actuator", "SimulatedMotor", "SimulatedGripper"]
