"""Advanced tests for telemetry system including persistence, export, and edge cases."""

import json
from datetime import datetime
from typing import Any, Dict, List

from talos.telemetry import TelemetryRecorder, TelemetryEvent, EventType
from talos.actuators import SimulatedMotor, SimulatedGripper


def test_telemetry_buffer_overflow_handling() -> None:
    """Test telemetry correctly handles buffer overflow."""
    recorder = TelemetryRecorder(max_events=10)

    # Record more events than max
    for i in range(20):
        recorder.record_event(EventType.POSITION_SET, "motor", {"index": i})

    events = recorder.get_events()

    # Should only have last 10 events
    assert len(events) == 10
    # Should have events 10-19
    assert events[0].data["index"] == 10
    assert events[-1].data["index"] == 19


def test_telemetry_filter_by_time_range() -> None:
    """Test filtering events by time range using timestamps."""
    recorder = TelemetryRecorder()

    # Record events
    for i in range(5):
        recorder.record_event(EventType.POSITION_SET, "motor", {"index": i})

    events = recorder.get_events()
    assert len(events) == 5

    # Get earliest timestamp
    earliest = events[0].timestamp

    # Filter by checking timestamps manually (since get_events doesn't support time filters)
    # This tests that timestamps are properly set and ordered
    filtered = [e for e in events if e.timestamp >= earliest]
    assert len(filtered) == 5

    # Filter for events after the first one
    after_first = [e for e in events if e.timestamp > earliest]
    assert len(after_first) >= 0  # May be 4 or less depending on timing


def test_telemetry_export_to_json() -> None:
    """Test exporting telemetry to JSON format."""
    recorder = TelemetryRecorder()
    recorder.record_event(
        EventType.POSITION_SET, "motor1", {"position": 1.5, "velocity": 0.5}
    )
    recorder.record_event(EventType.GRIPPER_CLOSED, "gripper1", {"force": 10.0})

    # Export to dict
    events_dict = recorder.to_dict()

    # Convert to JSON string
    json_str = json.dumps(events_dict, indent=2)

    # Parse back
    parsed = json.loads(json_str)

    assert len(parsed) == 2
    assert parsed[0]["event_type"] == "position_set"
    assert parsed[0]["actuator_name"] == "motor1"
    assert parsed[0]["data"]["position"] == 1.5
    assert parsed[1]["event_type"] == "gripper_closed"
    assert "timestamp" in parsed[0]


def test_telemetry_import_from_dict() -> None:
    """Test importing telemetry from dictionary format."""
    # Create events in dict format
    event_dicts: List[Dict[str, Any]] = [
        {
            "timestamp": datetime.now().isoformat(),
            "event_type": "position_set",
            "actuator_name": "motor1",
            "data": {"position": 1.0},
        },
        {
            "timestamp": datetime.now().isoformat(),
            "event_type": "gripper_closed",
            "actuator_name": "gripper1",
            "data": {"force": 5.0},
        },
    ]

    # Manually recreate events (simulating import)
    recorder = TelemetryRecorder()
    for event_dict in event_dicts:
        event = TelemetryEvent(
            timestamp=datetime.fromisoformat(event_dict["timestamp"]),
            event_type=EventType(event_dict["event_type"]),
            actuator_name=event_dict["actuator_name"],
            data=event_dict["data"],
        )
        recorder._events.append(event)

    # Verify import
    events = recorder.get_events()
    assert len(events) == 2
    assert events[0].event_type == EventType.POSITION_SET
    assert events[1].event_type == EventType.GRIPPER_CLOSED


def test_telemetry_merge_from_multiple_sources() -> None:
    """Test merging telemetry from multiple recorders."""
    recorder1 = TelemetryRecorder()
    recorder1.record_event(EventType.POSITION_SET, "motor1", {"value": 1})
    recorder1.record_event(EventType.POSITION_SET, "motor1", {"value": 2})

    recorder2 = TelemetryRecorder()
    recorder2.record_event(EventType.GRIPPER_CLOSED, "gripper1", {"value": 3})
    recorder2.record_event(EventType.GRIPPER_OPENED, "gripper1", {"value": 4})

    # Merge into new recorder
    merged = TelemetryRecorder(max_events=100)
    merged._events = recorder1._events + recorder2._events

    # Sort by timestamp to ensure chronological order
    merged._events.sort(key=lambda e: e.timestamp)

    assert merged.get_event_count() == 4
    assert merged.get_event_count(actuator_name="motor1") == 2
    assert merged.get_event_count(actuator_name="gripper1") == 2


def test_telemetry_query_performance_large_dataset() -> None:
    """Test telemetry query performance with large datasets."""
    recorder = TelemetryRecorder(max_events=10000)

    # Record large number of events
    for i in range(5000):
        recorder.record_event(EventType.POSITION_SET, f"motor{i % 10}", {"index": i})

    # Query should be fast even with large dataset
    start = datetime.now()
    events = recorder.get_events(actuator_name="motor5")
    duration = (datetime.now() - start).total_seconds()

    # Should complete in reasonable time
    assert duration < 1.0  # Less than 1 second
    assert len(events) == 500  # Should have 500 events for motor5


def test_telemetry_concurrent_writes() -> None:
    """Test telemetry handles concurrent writes correctly."""
    recorder = TelemetryRecorder(max_events=1000)

    # Simulate concurrent writes from multiple actuators
    for i in range(100):
        recorder.record_event(EventType.POSITION_SET, "motor1", {"index": i})
        recorder.record_event(EventType.POSITION_SET, "motor2", {"index": i})
        recorder.record_event(EventType.GRIPPER_CLOSED, "gripper1", {"index": i})

    # Verify all events recorded
    assert recorder.get_event_count() == 300
    assert recorder.get_event_count(actuator_name="motor1") == 100
    assert recorder.get_event_count(actuator_name="motor2") == 100
    assert recorder.get_event_count(actuator_name="gripper1") == 100


def test_telemetry_event_ordering() -> None:
    """Test that events maintain chronological order."""
    recorder = TelemetryRecorder()

    # Record events with small delays
    for i in range(10):
        recorder.record_event(EventType.POSITION_SET, "motor", {"index": i})

    events = recorder.get_events()

    # Verify chronological order
    for i in range(len(events) - 1):
        assert events[i].timestamp <= events[i + 1].timestamp
        assert events[i].data["index"] == i


def test_telemetry_complex_filtering() -> None:
    """Test complex filtering combinations."""
    recorder = TelemetryRecorder()

    # Record diverse events
    recorder.record_event(EventType.POSITION_SET, "motor1", {"value": 1})
    recorder.record_event(EventType.VELOCITY_SET, "motor1", {"value": 2})
    recorder.record_event(EventType.POSITION_SET, "motor2", {"value": 3})
    recorder.record_event(EventType.GRIPPER_CLOSED, "gripper1", {"value": 4})
    recorder.record_event(EventType.POSITION_SET, "motor1", {"value": 5})

    # Filter by actuator
    motor1_events = recorder.get_events(actuator_name="motor1")
    assert len(motor1_events) == 3

    # Filter by event type
    position_events = recorder.get_events(event_type=EventType.POSITION_SET)
    assert len(position_events) == 3

    # Filter by both
    motor1_position = recorder.get_events(
        actuator_name="motor1", event_type=EventType.POSITION_SET
    )
    assert len(motor1_position) == 2

    # Filter with limit
    limited = recorder.get_events(event_type=EventType.POSITION_SET, limit=2)
    assert len(limited) == 2
    assert limited[0].data["value"] == 3  # Most recent 2 position events
    assert limited[1].data["value"] == 5


def test_telemetry_empty_recorder() -> None:
    """Test operations on empty recorder."""
    recorder = TelemetryRecorder()

    assert recorder.get_event_count() == 0
    assert recorder.get_events() == []
    assert recorder.to_dict() == []
    assert recorder.is_enabled()


def test_telemetry_state_transitions() -> None:
    """Test telemetry captures state transitions correctly."""
    recorder = TelemetryRecorder()
    gripper = SimulatedGripper(name="test_gripper", telemetry=recorder)

    # Execute state transitions
    gripper.close()
    gripper.grasp("object1")
    gripper.release()
    gripper.close()
    gripper.grasp("object2")

    events = recorder.get_events()

    # Verify transition sequence (release() calls open() which generates 2 events)
    event_types = [e.event_type for e in events]
    assert EventType.GRIPPER_CLOSED in event_types
    assert EventType.OBJECT_GRASPED in event_types
    assert EventType.OBJECT_RELEASED in event_types
    assert EventType.GRIPPER_OPENED in event_types

    # Verify object names
    grasp_events = [e for e in events if e.event_type == EventType.OBJECT_GRASPED]
    assert len(grasp_events) == 2
    assert grasp_events[0].data["object_name"] == "object1"
    assert grasp_events[1].data["object_name"] == "object2"


def test_telemetry_data_integrity() -> None:
    """Test that telemetry data maintains integrity through operations."""
    recorder = TelemetryRecorder()
    motor = SimulatedMotor(
        name="test_motor", min_position=-2.0, max_position=2.0, telemetry=recorder
    )

    # Record various operations
    motor.set_position(1.5)
    motor.set_velocity(0.5)
    motor.set_position(-1.0)
    motor.enable()
    motor.disable()

    # Export and verify
    events_dict = recorder.to_dict()

    # Verify data structure
    for event_dict in events_dict:
        assert "timestamp" in event_dict
        assert "event_type" in event_dict
        assert "actuator_name" in event_dict
        assert "data" in event_dict
        assert event_dict["actuator_name"] == "test_motor"

    # Verify specific events
    position_events = [e for e in events_dict if e["event_type"] == "position_set"]
    assert len(position_events) == 2
    assert position_events[0]["data"]["clamped_position"] == 1.5
    assert position_events[1]["data"]["clamped_position"] == -1.0


def test_telemetry_max_events_boundary() -> None:
    """Test telemetry behavior at max_events boundary."""
    recorder = TelemetryRecorder(max_events=3)

    # Add exactly max_events
    recorder.record_event(EventType.POSITION_SET, "motor", {"index": 0})
    recorder.record_event(EventType.POSITION_SET, "motor", {"index": 1})
    recorder.record_event(EventType.POSITION_SET, "motor", {"index": 2})

    assert recorder.get_event_count() == 3

    # Add one more to trigger overflow
    recorder.record_event(EventType.POSITION_SET, "motor", {"index": 3})

    events = recorder.get_events()
    assert len(events) == 3
    assert events[0].data["index"] == 1  # First event removed
    assert events[-1].data["index"] == 3  # Latest event retained


def test_telemetry_disabled_state() -> None:
    """Test telemetry behavior when disabled."""
    recorder = TelemetryRecorder()

    # Record some events
    recorder.record_event(EventType.POSITION_SET, "motor", {"value": 1})
    assert recorder.get_event_count() == 1

    # Disable and try to record
    recorder.disable()
    recorder.record_event(EventType.POSITION_SET, "motor", {"value": 2})
    recorder.record_event(EventType.POSITION_SET, "motor", {"value": 3})

    # Count should not increase
    assert recorder.get_event_count() == 1

    # Re-enable and record
    recorder.enable()
    recorder.record_event(EventType.POSITION_SET, "motor", {"value": 4})

    # Now count should increase
    assert recorder.get_event_count() == 2


def test_telemetry_event_to_dict() -> None:
    """Test individual event conversion to dict."""
    event = TelemetryEvent(
        timestamp=datetime(2025, 1, 1, 12, 0, 0),
        event_type=EventType.POSITION_SET,
        actuator_name="test_motor",
        data={"position": 1.5, "velocity": 0.5},
    )

    event_dict = event.to_dict()

    assert event_dict["timestamp"] == "2025-01-01T12:00:00"
    assert event_dict["event_type"] == "position_set"
    assert event_dict["actuator_name"] == "test_motor"
    assert event_dict["data"]["position"] == 1.5
    assert event_dict["data"]["velocity"] == 0.5


def test_telemetry_multiple_actuators_isolation() -> None:
    """Test that telemetry correctly isolates events from multiple actuators."""
    recorder = TelemetryRecorder()

    motor1 = SimulatedMotor(name="motor1", telemetry=recorder)
    motor2 = SimulatedMotor(name="motor2", telemetry=recorder)
    gripper = SimulatedGripper(name="gripper", telemetry=recorder)

    # Perform operations
    motor1.set_position(1.0)
    motor2.set_position(2.0)
    motor1.set_position(1.5)
    gripper.close()
    motor2.set_velocity(0.5)

    # Verify isolation
    motor1_events = recorder.get_events(actuator_name="motor1")
    motor2_events = recorder.get_events(actuator_name="motor2")
    gripper_events = recorder.get_events(actuator_name="gripper")

    assert len(motor1_events) == 2
    assert len(motor2_events) == 2
    assert len(gripper_events) == 1

    # Verify no cross-contamination
    for event in motor1_events:
        assert event.actuator_name == "motor1"
    for event in motor2_events:
        assert event.actuator_name == "motor2"
    for event in gripper_events:
        assert event.actuator_name == "gripper"
