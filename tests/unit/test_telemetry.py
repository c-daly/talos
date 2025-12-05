"""Tests for telemetry system."""

from talos.telemetry import TelemetryRecorder, EventType
from talos.actuators import SimulatedMotor, SimulatedGripper


def test_telemetry_recorder_initialization() -> None:
    """Test telemetry recorder initialization."""
    recorder = TelemetryRecorder(max_events=100)
    assert recorder.max_events == 100
    assert recorder.is_enabled()
    assert recorder.get_event_count() == 0


def test_telemetry_record_event() -> None:
    """Test recording telemetry events."""
    recorder = TelemetryRecorder()
    recorder.record_event(
        EventType.POSITION_SET, "test_motor", {"position": 1.5, "velocity": 0.0}
    )

    events = recorder.get_events()
    assert len(events) == 1
    assert events[0].event_type == EventType.POSITION_SET
    assert events[0].actuator_name == "test_motor"
    assert events[0].data["position"] == 1.5


def test_telemetry_filter_by_actuator() -> None:
    """Test filtering events by actuator name."""
    recorder = TelemetryRecorder()
    recorder.record_event(EventType.POSITION_SET, "motor1", {})
    recorder.record_event(EventType.POSITION_SET, "motor2", {})
    recorder.record_event(EventType.VELOCITY_SET, "motor1", {})

    motor1_events = recorder.get_events(actuator_name="motor1")
    assert len(motor1_events) == 2

    motor2_events = recorder.get_events(actuator_name="motor2")
    assert len(motor2_events) == 1


def test_telemetry_filter_by_event_type() -> None:
    """Test filtering events by event type."""
    recorder = TelemetryRecorder()
    recorder.record_event(EventType.POSITION_SET, "motor1", {})
    recorder.record_event(EventType.VELOCITY_SET, "motor1", {})
    recorder.record_event(EventType.POSITION_SET, "motor2", {})

    position_events = recorder.get_events(event_type=EventType.POSITION_SET)
    assert len(position_events) == 2

    velocity_events = recorder.get_events(event_type=EventType.VELOCITY_SET)
    assert len(velocity_events) == 1


def test_telemetry_limit() -> None:
    """Test limiting number of returned events."""
    recorder = TelemetryRecorder()
    for i in range(10):
        recorder.record_event(EventType.POSITION_SET, "motor", {"index": i})

    limited_events = recorder.get_events(limit=5)
    assert len(limited_events) == 5
    # Should get the most recent 5 events (indices 5-9)
    assert limited_events[0].data["index"] == 5
    assert limited_events[-1].data["index"] == 9


def test_telemetry_max_events() -> None:
    """Test that telemetry respects max_events limit."""
    recorder = TelemetryRecorder(max_events=5)
    for i in range(10):
        recorder.record_event(EventType.POSITION_SET, "motor", {"index": i})

    # Should only have the last 5 events
    events = recorder.get_events()
    assert len(events) == 5
    assert events[0].data["index"] == 5
    assert events[-1].data["index"] == 9


def test_telemetry_clear() -> None:
    """Test clearing telemetry events."""
    recorder = TelemetryRecorder()
    recorder.record_event(EventType.POSITION_SET, "motor", {})
    recorder.record_event(EventType.VELOCITY_SET, "motor", {})

    assert recorder.get_event_count() == 2

    recorder.clear()
    assert recorder.get_event_count() == 0


def test_telemetry_enable_disable() -> None:
    """Test enabling and disabling telemetry."""
    recorder = TelemetryRecorder()
    assert recorder.is_enabled()

    recorder.disable()
    assert not recorder.is_enabled()

    # Events should not be recorded when disabled
    recorder.record_event(EventType.POSITION_SET, "motor", {})
    assert recorder.get_event_count() == 0

    recorder.enable()
    recorder.record_event(EventType.POSITION_SET, "motor", {})
    assert recorder.get_event_count() == 1


def test_telemetry_to_dict() -> None:
    """Test exporting telemetry to dictionary."""
    recorder = TelemetryRecorder()
    recorder.record_event(EventType.POSITION_SET, "motor", {"position": 1.5})

    events_dict = recorder.to_dict()
    assert len(events_dict) == 1
    assert events_dict[0]["event_type"] == "position_set"
    assert events_dict[0]["actuator_name"] == "motor"
    assert events_dict[0]["data"]["position"] == 1.5
    assert "timestamp" in events_dict[0]


def test_motor_telemetry_position_set() -> None:
    """Test motor position telemetry."""
    recorder = TelemetryRecorder()
    motor = SimulatedMotor(name="test_motor", telemetry=recorder)

    motor.set_position(1.5)

    events = recorder.get_events(event_type=EventType.POSITION_SET)
    assert len(events) == 1
    assert events[0].actuator_name == "test_motor"
    assert events[0].data["clamped_position"] == 1.5


def test_motor_telemetry_velocity_set() -> None:
    """Test motor velocity telemetry."""
    recorder = TelemetryRecorder()
    motor = SimulatedMotor(name="test_motor", telemetry=recorder)

    motor.set_velocity(0.5)

    events = recorder.get_events(event_type=EventType.VELOCITY_SET)
    assert len(events) == 1
    assert events[0].actuator_name == "test_motor"
    assert events[0].data["clamped_velocity"] == 0.5


def test_motor_telemetry_position_clamping() -> None:
    """Test motor telemetry records clamping."""
    recorder = TelemetryRecorder()
    motor = SimulatedMotor(
        name="test_motor", min_position=-1.0, max_position=1.0, telemetry=recorder
    )

    # Set position beyond max
    motor.set_position(2.0)

    events = recorder.get_events(event_type=EventType.POSITION_SET)
    assert len(events) == 1
    assert events[0].data["requested_position"] == 2.0
    assert events[0].data["clamped_position"] == 1.0


def test_gripper_telemetry_open() -> None:
    """Test gripper open telemetry."""
    recorder = TelemetryRecorder()
    gripper = SimulatedGripper(name="test_gripper", telemetry=recorder)

    gripper.close()
    gripper.open()

    open_events = recorder.get_events(event_type=EventType.GRIPPER_OPENED)
    assert len(open_events) == 1
    assert open_events[0].actuator_name == "test_gripper"


def test_gripper_telemetry_close() -> None:
    """Test gripper close telemetry."""
    recorder = TelemetryRecorder()
    gripper = SimulatedGripper(name="test_gripper", telemetry=recorder)

    gripper.close()

    close_events = recorder.get_events(event_type=EventType.GRIPPER_CLOSED)
    assert len(close_events) == 1
    assert close_events[0].actuator_name == "test_gripper"
    assert "force" in close_events[0].data


def test_gripper_telemetry_grasp() -> None:
    """Test gripper grasp telemetry."""
    recorder = TelemetryRecorder()
    gripper = SimulatedGripper(name="test_gripper", telemetry=recorder)

    gripper.close()
    gripper.grasp("cup")

    grasp_events = recorder.get_events(event_type=EventType.OBJECT_GRASPED)
    assert len(grasp_events) == 1
    assert grasp_events[0].actuator_name == "test_gripper"
    assert grasp_events[0].data["object_name"] == "cup"
    assert grasp_events[0].data["success"] is True


def test_gripper_telemetry_failed_grasp() -> None:
    """Test gripper telemetry records failed grasp."""
    recorder = TelemetryRecorder()
    gripper = SimulatedGripper(name="test_gripper", telemetry=recorder)

    # Try to grasp while open
    gripper.grasp("cup")

    grasp_events = recorder.get_events(event_type=EventType.OBJECT_GRASPED)
    assert len(grasp_events) == 1
    assert grasp_events[0].data["success"] is False


def test_gripper_telemetry_release() -> None:
    """Test gripper release telemetry."""
    recorder = TelemetryRecorder()
    gripper = SimulatedGripper(name="test_gripper", telemetry=recorder)

    gripper.close()
    gripper.grasp("cup")
    gripper.release()

    release_events = recorder.get_events(event_type=EventType.OBJECT_RELEASED)
    assert len(release_events) == 1
    assert release_events[0].data["object_name"] == "cup"


def test_multiple_actuators_shared_telemetry() -> None:
    """Test multiple actuators sharing a telemetry recorder."""
    recorder = TelemetryRecorder()
    motor1 = SimulatedMotor(name="motor1", telemetry=recorder)
    motor2 = SimulatedMotor(name="motor2", telemetry=recorder)
    gripper = SimulatedGripper(name="gripper", telemetry=recorder)

    motor1.set_position(1.0)
    motor2.set_position(2.0)
    gripper.close()

    # All events should be in the same recorder
    assert recorder.get_event_count() == 3

    # Can filter by actuator
    motor1_events = recorder.get_events(actuator_name="motor1")
    assert len(motor1_events) == 1

    motor2_events = recorder.get_events(actuator_name="motor2")
    assert len(motor2_events) == 1

    gripper_events = recorder.get_events(actuator_name="gripper")
    assert len(gripper_events) == 1
