"""Tests for actuator feedback loops and coordination."""

import pytest

from talos.actuators import SimulatedMotor, SimulatedGripper
from talos.telemetry import TelemetryRecorder, EventType


def test_motor_position_feedback_accuracy() -> None:
    """Test motor position feedback accuracy."""
    motor = SimulatedMotor(name="test_motor")

    # Set position and verify feedback
    motor.set_position(1.5)
    assert motor.get_position() == 1.5

    motor.set_position(-0.5)
    assert motor.get_position() == -0.5

    # Test clamping feedback
    motor.set_position(5.0)  # Beyond max
    assert motor.get_position() == motor.max_position


def test_gripper_force_feedback() -> None:
    """Test gripper force feedback."""
    telemetry = TelemetryRecorder()
    gripper = SimulatedGripper(name="test_gripper", telemetry=telemetry)

    # Close gripper with specific force and check force feedback
    test_force = 0.75
    gripper.close(force=test_force)

    events = telemetry.get_events(event_type=EventType.GRIPPER_CLOSED)
    assert len(events) == 1
    assert "force" in events[0].data
    assert events[0].data["force"] == test_force


def test_gripper_grasp_success_detection() -> None:
    """Test gripper grasp success detection."""
    telemetry = TelemetryRecorder()
    gripper = SimulatedGripper(name="test_gripper", telemetry=telemetry)

    # Successful grasp (gripper closed)
    gripper.close()
    gripper.grasp("cup")

    grasp_events = telemetry.get_events(event_type=EventType.OBJECT_GRASPED)
    assert len(grasp_events) == 1
    assert grasp_events[0].data["success"] is True
    assert gripper.get_grasped_object() == "cup"

    # Failed grasp (gripper open)
    gripper.release()
    gripper.open()
    gripper.grasp("block")

    grasp_events = telemetry.get_events(event_type=EventType.OBJECT_GRASPED)
    assert len(grasp_events) == 2
    assert grasp_events[1].data["success"] is False
    assert gripper.get_grasped_object() is None


def test_actuator_error_recovery() -> None:
    """Test actuator error recovery."""
    motor = SimulatedMotor(name="test_motor")

    # Disable motor (simulating error state)
    motor.disable()
    assert not motor.is_enabled()

    # Attempt operation (should fail)
    with pytest.raises(RuntimeError):
        motor.set_position(1.0)

    # Recover by re-enabling
    motor.enable()
    assert motor.is_enabled()

    # Should work now
    motor.set_position(1.0)
    assert motor.get_position() == 1.0


def test_actuator_telemetry_generation() -> None:
    """Test actuator telemetry generation."""
    telemetry = TelemetryRecorder()
    motor = SimulatedMotor(name="motor", telemetry=telemetry)
    gripper = SimulatedGripper(name="gripper", telemetry=telemetry)

    # Perform operations
    motor.set_position(1.0)
    motor.set_velocity(0.5)
    gripper.close()
    gripper.grasp("object")

    # Verify telemetry generated
    assert telemetry.get_event_count() >= 4

    motor_events = telemetry.get_events(actuator_name="motor")
    gripper_events = telemetry.get_events(actuator_name="gripper")

    assert len(motor_events) >= 2
    assert len(gripper_events) >= 2


def test_multi_actuator_coordination() -> None:
    """Test multi-actuator coordination."""
    telemetry = TelemetryRecorder()
    motor1 = SimulatedMotor(name="joint1", telemetry=telemetry)
    motor2 = SimulatedMotor(name="joint2", telemetry=telemetry)
    motor3 = SimulatedMotor(name="joint3", telemetry=telemetry)
    gripper = SimulatedGripper(name="gripper", telemetry=telemetry)

    # Coordinate movement of arm (3 joints + gripper)
    # Move to position
    motor1.set_position(0.5)
    motor2.set_position(1.0)
    motor3.set_position(1.5)

    # Close gripper
    gripper.close()
    gripper.grasp("object")

    # Verify coordination
    assert motor1.get_position() == 0.5
    assert motor2.get_position() == 1.0
    assert motor3.get_position() == 1.5
    assert gripper.is_grasping()
    assert gripper.get_grasped_object() == "object"

    # Verify telemetry captured all operations
    assert telemetry.get_event_count() >= 5


def test_actuator_velocity_control() -> None:
    """Test motor velocity control and feedback."""
    telemetry = TelemetryRecorder()
    motor = SimulatedMotor(name="test_motor", telemetry=telemetry)

    # Set velocities
    velocities = [0.1, 0.5, 1.0, 0.0]
    for vel in velocities:
        motor.set_velocity(vel)

    # Verify feedback
    events = telemetry.get_events(event_type=EventType.VELOCITY_SET)
    assert len(events) == len(velocities)

    for i, event in enumerate(events):
        assert event.data["clamped_velocity"] == velocities[i]


def test_actuator_position_clamping_feedback() -> None:
    """Test that position clamping provides proper feedback."""
    telemetry = TelemetryRecorder()
    motor = SimulatedMotor(
        name="test_motor",
        min_position=-1.0,
        max_position=1.0,
        telemetry=telemetry,
    )

    # Try to set beyond limits
    motor.set_position(2.0)
    motor.set_position(-2.0)

    events = telemetry.get_events(event_type=EventType.POSITION_SET)

    # First command clamped to max
    assert events[0].data["requested_position"] == 2.0
    assert events[0].data["clamped_position"] == 1.0

    # Second command clamped to min
    assert events[1].data["requested_position"] == -2.0
    assert events[1].data["clamped_position"] == -1.0


def test_gripper_state_transitions() -> None:
    """Test gripper state transitions and feedback."""
    telemetry = TelemetryRecorder()
    gripper = SimulatedGripper(name="test_gripper", telemetry=telemetry)

    # Open -> Close -> Grasp -> Release -> Open
    gripper.open()
    gripper.close()
    gripper.grasp("object")
    gripper.release()
    gripper.open()

    # Verify state transitions in telemetry
    events = telemetry.get_events()
    event_types = [e.event_type for e in events]

    assert EventType.GRIPPER_OPENED in event_types
    assert EventType.GRIPPER_CLOSED in event_types
    assert EventType.OBJECT_GRASPED in event_types
    assert EventType.OBJECT_RELEASED in event_types


def test_gripper_force_limits() -> None:
    """Test gripper respects force limits."""
    telemetry = TelemetryRecorder()
    gripper = SimulatedGripper(name="test_gripper", telemetry=telemetry)

    # Close gripper multiple times with varying forces
    test_forces = [0.1, 0.5, 0.75, 1.0, 0.25]
    for force in test_forces:
        gripper.open()
        gripper.close(force=force)

    # Check all force readings are recorded correctly
    events = telemetry.get_events(event_type=EventType.GRIPPER_CLOSED)
    assert len(events) == len(test_forces)
    for i, event in enumerate(events):
        assert event.data["force"] == test_forces[i]
        assert 0.0 <= event.data["force"] <= 1.0


def test_motor_smooth_motion() -> None:
    """Test motor smooth motion through multiple positions."""
    telemetry = TelemetryRecorder()
    motor = SimulatedMotor(name="test_motor", telemetry=telemetry)

    # Move through a series of positions
    positions = [0.0, 0.25, 0.5, 0.75, 1.0, 0.75, 0.5, 0.25, 0.0]
    for pos in positions:
        motor.set_position(pos)

    # Verify all positions reached
    events = telemetry.get_events(event_type=EventType.POSITION_SET)
    assert len(events) == len(positions)

    for i, event in enumerate(events):
        assert event.data["clamped_position"] == positions[i]


def test_actuator_disable_mid_operation() -> None:
    """Test disabling actuator mid-operation."""
    motor = SimulatedMotor(name="test_motor")

    # Start operation
    motor.set_position(1.0)
    assert motor.get_position() == 1.0

    # Disable mid-operation
    motor.disable()

    # Should maintain last position
    assert motor.get_position() == 1.0

    # Further commands should fail
    with pytest.raises(RuntimeError):
        motor.set_position(2.0)


def test_gripper_multiple_grasp_release_cycles() -> None:
    """Test gripper through multiple grasp-release cycles."""
    telemetry = TelemetryRecorder()
    gripper = SimulatedGripper(name="test_gripper", telemetry=telemetry)

    objects = ["cup", "block", "sphere", "cylinder"]

    for obj in objects:
        gripper.close()
        gripper.grasp(obj)
        assert gripper.get_grasped_object() == obj

        gripper.release()
        assert gripper.get_grasped_object() is None

        gripper.open()

    # Verify telemetry
    grasp_events = telemetry.get_events(event_type=EventType.OBJECT_GRASPED)
    release_events = telemetry.get_events(event_type=EventType.OBJECT_RELEASED)

    assert len(grasp_events) == len(objects)
    assert len(release_events) == len(objects)


def test_actuator_info_includes_state() -> None:
    """Test actuator info includes current state."""
    motor = SimulatedMotor(name="test_motor")
    gripper = SimulatedGripper(name="test_gripper")

    motor.set_position(1.5)
    gripper.close()

    motor_info = motor.get_info()
    gripper_info = gripper.get_info()

    # Verify info includes state
    assert "enabled" in motor_info
    assert "name" in motor_info
    assert motor_info["enabled"] is True

    assert "enabled" in gripper_info
    assert "name" in gripper_info
    assert gripper_info["enabled"] is True
