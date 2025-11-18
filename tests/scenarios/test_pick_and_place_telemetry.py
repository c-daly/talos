"""Integration tests for pick and place scenario with telemetry."""

from talos.scenarios import PickAndPlaceScenario
from talos.telemetry import EventType


def test_pick_and_place_telemetry_tracking() -> None:
    """Test that pick and place scenario tracks telemetry."""
    scenario = PickAndPlaceScenario()

    # Execute a pick and place operation
    scenario.move_to_object("cup")
    scenario.grasp_object("cup")
    scenario.move_to_location("shelf")
    scenario.release_object()

    # Should have recorded multiple events
    assert scenario.telemetry.get_event_count() > 0


def test_pick_and_place_motor_telemetry() -> None:
    """Test motor telemetry in pick and place scenario."""
    scenario = PickAndPlaceScenario()

    scenario.move_to_object("cup")

    # Should have position set events for the motors
    position_events = scenario.telemetry.get_events(event_type=EventType.POSITION_SET)
    assert len(position_events) >= 3  # At least one for each joint


def test_pick_and_place_gripper_telemetry() -> None:
    """Test gripper telemetry in pick and place scenario."""
    scenario = PickAndPlaceScenario()

    scenario.move_to_object("cup")
    scenario.grasp_object("cup")

    # Should have gripper events
    grasp_events = scenario.telemetry.get_events(event_type=EventType.OBJECT_GRASPED)
    assert len(grasp_events) == 1
    assert grasp_events[0].data["object_name"] == "cup"


def test_pick_and_place_complete_sequence_telemetry() -> None:
    """Test telemetry for complete pick and place sequence."""
    scenario = PickAndPlaceScenario()

    scenario.execute_pick_and_place("cup", "shelf")

    # Check for various event types
    position_events = scenario.telemetry.get_events(event_type=EventType.POSITION_SET)
    assert len(position_events) > 0

    grasp_events = scenario.telemetry.get_events(event_type=EventType.OBJECT_GRASPED)
    assert len(grasp_events) == 1

    release_events = scenario.telemetry.get_events(event_type=EventType.OBJECT_RELEASED)
    assert len(release_events) == 1


def test_pick_and_place_reset_clears_telemetry() -> None:
    """Test that reset clears telemetry."""
    scenario = PickAndPlaceScenario()

    scenario.move_to_object("cup")
    scenario.grasp_object("cup")

    # Should have events
    assert scenario.telemetry.get_event_count() > 0

    scenario.reset()

    # Telemetry should be cleared
    assert scenario.telemetry.get_event_count() == 0


def test_pick_and_place_telemetry_event_order() -> None:
    """Test that telemetry events are in correct order."""
    scenario = PickAndPlaceScenario()

    scenario.move_to_object("cup")
    scenario.grasp_object("cup")
    scenario.release_object()

    # Get all events
    all_events = scenario.telemetry.get_events()

    # Find key events and verify order
    event_types = [e.event_type for e in all_events]

    grasp_index = event_types.index(EventType.OBJECT_GRASPED)
    release_index = event_types.index(EventType.OBJECT_RELEASED)

    # Grasp should come before release
    assert grasp_index < release_index


def test_pick_and_place_telemetry_in_state() -> None:
    """Test that telemetry event count is included in state."""
    scenario = PickAndPlaceScenario()

    initial_state = scenario.get_state()
    assert "telemetry_event_count" in initial_state
    assert initial_state["telemetry_event_count"] == 0

    scenario.move_to_object("cup")
    scenario.grasp_object("cup")

    updated_state = scenario.get_state()
    assert updated_state["telemetry_event_count"] > 0


def test_pick_and_place_filter_telemetry_by_actuator() -> None:
    """Test filtering telemetry by specific actuator."""
    scenario = PickAndPlaceScenario()

    scenario.move_to_object("cup")
    scenario.grasp_object("cup")

    # Get gripper-specific events
    gripper_events = scenario.telemetry.get_events(actuator_name="gripper")
    assert len(gripper_events) > 0

    # All events should be from the gripper
    for event in gripper_events:
        assert event.actuator_name == "gripper"

    # Get joint1-specific events
    joint1_events = scenario.telemetry.get_events(actuator_name="joint1")
    assert len(joint1_events) > 0

    # All events should be from joint1
    for event in joint1_events:
        assert event.actuator_name == "joint1"


def test_pick_and_place_telemetry_export() -> None:
    """Test exporting telemetry data."""
    scenario = PickAndPlaceScenario()

    scenario.move_to_object("cup")
    scenario.grasp_object("cup")

    # Export telemetry as dictionaries
    telemetry_dict = scenario.telemetry.to_dict()

    assert len(telemetry_dict) > 0
    assert isinstance(telemetry_dict, list)

    # Check structure of exported events
    for event in telemetry_dict:
        assert "timestamp" in event
        assert "event_type" in event
        assert "actuator_name" in event
        assert "data" in event
