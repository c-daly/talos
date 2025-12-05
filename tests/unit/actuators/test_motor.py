"""Tests for simulated motor actuator."""

import pytest
from talos.actuators.motor import SimulatedMotor


def test_motor_initialization() -> None:
    """Test motor initialization."""
    motor = SimulatedMotor(
        name="test_motor", min_position=-1.0, max_position=1.0, max_velocity=2.0
    )
    assert motor.name == "test_motor"
    assert motor.min_position == -1.0
    assert motor.max_position == 1.0
    assert motor.max_velocity == 2.0


def test_motor_set_position() -> None:
    """Test motor position setting."""
    motor = SimulatedMotor(min_position=-3.14, max_position=3.14)

    motor.set_position(1.5)
    assert motor.get_position() == 1.5

    motor.set_position(-1.0)
    assert motor.get_position() == -1.0


def test_motor_position_clamping() -> None:
    """Test that motor position is clamped to valid range."""
    motor = SimulatedMotor(min_position=-1.0, max_position=1.0)

    # Set beyond max
    motor.set_position(2.0)
    assert motor.get_position() == 1.0

    # Set below min
    motor.set_position(-2.0)
    assert motor.get_position() == -1.0


def test_motor_set_velocity() -> None:
    """Test motor velocity setting."""
    motor = SimulatedMotor(max_velocity=1.0)

    motor.set_velocity(0.5)
    assert motor.get_velocity() == 0.5


def test_motor_velocity_clamping() -> None:
    """Test that motor velocity is clamped to valid range."""
    motor = SimulatedMotor(max_velocity=1.0)

    # Set beyond max
    motor.set_velocity(2.0)
    assert motor.get_velocity() == 1.0

    # Set below min
    motor.set_velocity(-2.0)
    assert motor.get_velocity() == -1.0


def test_motor_disabled() -> None:
    """Test that disabled motor raises error."""
    motor = SimulatedMotor()
    motor.disable()

    with pytest.raises(RuntimeError, match="disabled"):
        motor.set_position(1.0)

    with pytest.raises(RuntimeError, match="disabled"):
        motor.set_velocity(0.5)


def test_motor_get_state() -> None:
    """Test motor state retrieval."""
    motor = SimulatedMotor()
    motor.set_position(1.0)

    state = motor.get_state()
    assert state["position"] == 1.0
    assert state["target_position"] == 1.0
    assert "velocity" in state


def test_motor_get_info() -> None:
    """Test motor info retrieval."""
    motor = SimulatedMotor(
        name="test_motor",
        min_position=-2.0,
        max_position=2.0,
        max_velocity=1.5,
    )

    info = motor.get_info()
    assert info["name"] == "test_motor"
    assert info["type"] == "SimulatedMotor"
    assert info["enabled"] is True
    assert info["min_position"] == -2.0
    assert info["max_position"] == 2.0
    assert info["max_velocity"] == 1.5
