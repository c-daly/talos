"""Tests for simulated gripper actuator."""

import pytest
from talos.actuators.gripper import SimulatedGripper


def test_gripper_initialization() -> None:
    """Test gripper initialization."""
    gripper = SimulatedGripper(name="test_gripper", max_opening=0.1)
    assert gripper.name == "test_gripper"
    assert gripper.max_opening == 0.1


def test_gripper_open() -> None:
    """Test gripper opening."""
    gripper = SimulatedGripper(max_opening=0.08)

    # Close first
    gripper.close()
    state = gripper.get_state()
    assert state["opening"] == 0.0

    # Open
    gripper.open()
    state = gripper.get_state()
    assert state["opening"] == 0.08


def test_gripper_open_with_value() -> None:
    """Test gripper opening to specific width."""
    gripper = SimulatedGripper(max_opening=0.08)

    gripper.open(0.04)
    state = gripper.get_state()
    assert state["opening"] == 0.04


def test_gripper_close() -> None:
    """Test gripper closing."""
    gripper = SimulatedGripper()

    gripper.close()
    state = gripper.get_state()
    assert state["opening"] == 0.0


def test_gripper_grasp() -> None:
    """Test object grasping."""
    gripper = SimulatedGripper()

    # Must close before grasping
    gripper.close()
    success = gripper.grasp("cup")

    assert success
    assert gripper.is_grasping()
    assert gripper.get_grasped_object() == "cup"


def test_gripper_grasp_requires_closed() -> None:
    """Test that grasping requires gripper to be closed."""
    gripper = SimulatedGripper()

    # Try to grasp while open
    success = gripper.grasp("cup")

    assert not success
    assert not gripper.is_grasping()


def test_gripper_release() -> None:
    """Test object release."""
    gripper = SimulatedGripper()

    # Grasp an object
    gripper.close()
    gripper.grasp("cup")
    assert gripper.is_grasping()

    # Release
    gripper.release()
    assert not gripper.is_grasping()
    assert gripper.get_grasped_object() is None


def test_gripper_disabled() -> None:
    """Test that disabled gripper raises error."""
    gripper = SimulatedGripper()
    gripper.disable()

    with pytest.raises(RuntimeError, match="disabled"):
        gripper.open()

    with pytest.raises(RuntimeError, match="disabled"):
        gripper.close()

    with pytest.raises(RuntimeError, match="disabled"):
        gripper.grasp("cup")


def test_gripper_get_state() -> None:
    """Test gripper state retrieval."""
    gripper = SimulatedGripper()
    gripper.close()
    gripper.grasp("cup")

    state = gripper.get_state()
    assert state["opening"] == 0.0
    assert state["is_grasping"] is True
    assert state["grasped_object"] == "cup"
