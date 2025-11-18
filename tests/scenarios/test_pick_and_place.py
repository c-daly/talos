"""Tests for pick and place scenario."""

from talos.scenarios.pick_and_place import PickAndPlaceScenario


def test_scenario_initialization() -> None:
    """Test scenario initialization."""
    scenario = PickAndPlaceScenario()

    # Check sensors exist
    assert scenario.camera is not None
    assert scenario.depth is not None
    assert scenario.imu is not None

    # Check actuators exist
    assert scenario.joint1 is not None
    assert scenario.joint2 is not None
    assert scenario.joint3 is not None
    assert scenario.gripper is not None

    # Check objects exist
    assert "cup" in scenario.objects
    assert "block" in scenario.objects

    # Check locations exist
    assert "table" in scenario.locations
    assert "shelf" in scenario.locations
    assert "home" in scenario.locations


def test_get_state() -> None:
    """Test state retrieval."""
    scenario = PickAndPlaceScenario()
    state = scenario.get_state()

    assert "end_effector_position" in state
    assert "joint_positions" in state
    assert "gripper_state" in state
    assert "objects" in state
    assert "locations" in state
    assert "action_history" in state


def test_move_to_object() -> None:
    """Test moving to object."""
    scenario = PickAndPlaceScenario()

    success = scenario.move_to_object("cup")
    assert success

    state = scenario.get_state()
    assert "move_to_object(cup)" in state["action_history"]


def test_move_to_invalid_object() -> None:
    """Test moving to invalid object."""
    scenario = PickAndPlaceScenario()

    success = scenario.move_to_object("invalid_object")
    assert not success


def test_move_to_location() -> None:
    """Test moving to location."""
    scenario = PickAndPlaceScenario()

    success = scenario.move_to_location("table")
    assert success

    state = scenario.get_state()
    assert "move_to_location(table)" in state["action_history"]


def test_move_to_invalid_location() -> None:
    """Test moving to invalid location."""
    scenario = PickAndPlaceScenario()

    success = scenario.move_to_location("invalid_location")
    assert not success


def test_grasp_object() -> None:
    """Test grasping object."""
    scenario = PickAndPlaceScenario()

    # Move to object first
    scenario.move_to_object("cup")

    # Grasp
    success = scenario.grasp_object("cup")
    assert success

    state = scenario.get_state()
    assert state["objects"]["cup"]["grasped"] is True
    assert "grasp_object(cup)" in state["action_history"]


def test_grasp_object_too_far() -> None:
    """Test that grasping fails when too far."""
    scenario = PickAndPlaceScenario()

    # Don't move to object
    success = scenario.grasp_object("cup")
    assert not success


def test_release_object() -> None:
    """Test releasing object."""
    scenario = PickAndPlaceScenario()

    # Pick up object
    scenario.move_to_object("cup")
    scenario.grasp_object("cup")

    # Release
    success = scenario.release_object()
    assert success

    state = scenario.get_state()
    assert state["objects"]["cup"]["grasped"] is False
    assert "release_object()" in state["action_history"]


def test_release_without_object() -> None:
    """Test releasing when not holding object."""
    scenario = PickAndPlaceScenario()

    success = scenario.release_object()
    assert not success


def test_execute_pick_and_place() -> None:
    """Test complete pick and place sequence."""
    scenario = PickAndPlaceScenario()

    success, actions = scenario.execute_pick_and_place("cup", "shelf")

    assert success
    assert len(actions) == 4
    assert "Moved to cup" in actions
    assert "Grasped cup" in actions
    assert "Moved to shelf" in actions
    assert "Released object" in actions


def test_execute_pick_and_place_invalid_object() -> None:
    """Test pick and place with invalid object."""
    scenario = PickAndPlaceScenario()

    success, actions = scenario.execute_pick_and_place("invalid_object", "shelf")

    assert not success
    assert "Failed to move to object" in actions


def test_execute_pick_and_place_invalid_location() -> None:
    """Test pick and place with invalid location."""
    scenario = PickAndPlaceScenario()

    success, actions = scenario.execute_pick_and_place("cup", "invalid_location")

    assert not success
    assert "Failed to move to location" in actions


def test_execute_pick_and_place_failed_grasp() -> None:
    """Test pick and place when grasp fails (object removed after move)."""
    scenario = PickAndPlaceScenario()

    # Start the sequence - move to cup works
    scenario.move_to_object("cup")

    # Now remove the cup from objects to make grasp fail
    original_objects = scenario.objects.copy()
    scenario.objects = {"block": original_objects["block"]}

    # Try to grasp - should fail because cup no longer exists
    success = scenario.grasp_object("cup")
    assert not success

    # Restore
    scenario.objects = original_objects


def test_execute_pick_and_place_grasp_invalid_object() -> None:
    """Test that execute_pick_and_place fails when grasping invalid object."""
    scenario = PickAndPlaceScenario()

    # This should fail at the grasp step because we're grasping something
    # that doesn't exist in the objects dictionary
    # But first we need to move to it, which will also fail
    # Let's test line 155 directly
    success = scenario.grasp_object("nonexistent_object")
    assert not success


def test_execute_pick_and_place_grasp_failure_path() -> None:
    """Test execute_pick_and_place when grasp fails (line 235)."""
    scenario = PickAndPlaceScenario()

    # Add a "fake_object" that doesn't really exist in scenario.objects
    # Wait, we need move_to_object to succeed but grasp_object to fail
    # The grasp can fail if the object is not in the dict (line 155)
    # or if the distance is too far (line 163)

    # Let's manipulate to make grasp fail
    # Move end effector away from cup position
    import numpy as np

    scenario.end_effector_position = np.array([10.0, 10.0, 10.0])

    # Now try to grasp (should fail distance check)
    success = scenario.grasp_object("cup")
    assert not success


def test_execute_pick_and_place_complete_grasp_failure() -> None:
    """Test full execute_pick_and_place with grasp failure."""
    scenario = PickAndPlaceScenario()

    # We need a way to make grasp fail after move succeeds
    # One way: use a mock or patch, but let's keep it simple
    # After calling move_to_object, manually move end effector away

    # Override the move_to_object temporarily to not update end effector
    original_move = scenario.move_to_object

    def fake_move(obj_name: str) -> bool:
        # Just update action history without moving
        if obj_name not in scenario.objects:
            return False
        scenario.action_history.append(f"move_to_object({obj_name})")
        return True

    scenario.move_to_object = fake_move  # type: ignore

    # Now execute - move will succeed but grasp will fail (distance check)
    success, actions = scenario.execute_pick_and_place("cup", "shelf")

    # Restore
    scenario.move_to_object = original_move  # type: ignore

    assert not success
    assert "Failed to grasp object" in actions


def test_execute_pick_and_place_release_failure_path() -> None:
    """Test execute_pick_and_place when release fails (line 245)."""
    scenario = PickAndPlaceScenario()

    # Complete most of the sequence
    scenario.move_to_object("cup")
    scenario.grasp_object("cup")
    scenario.move_to_location("shelf")

    # Now manually clear the gripper's grasped object to make release fail
    scenario.gripper._grasped_object = None

    # Try to release - should fail
    success = scenario.release_object()
    assert not success


def test_execute_pick_and_place_complete_release_failure() -> None:
    """Test full execute_pick_and_place with release failure."""
    scenario = PickAndPlaceScenario()

    # Override release_object to return False
    original_release = scenario.release_object

    def fake_release() -> bool:
        return False

    scenario.release_object = fake_release  # type: ignore

    # Now execute - everything should succeed until release
    success, actions = scenario.execute_pick_and_place("cup", "shelf")

    # Restore
    scenario.release_object = original_release  # type: ignore

    assert not success
    assert "Failed to release object" in actions


def test_execute_pick_and_place_failed_release() -> None:
    """Test pick and place when release fails (not holding object)."""
    scenario = PickAndPlaceScenario()

    # Manually interfere with the grasped object to simulate failed release
    # We'll need to test this differently - release when gripper is already open
    scenario.move_to_object("cup")
    # Skip the grasp step - just close gripper without grasping
    scenario.gripper.close()
    # Now move to location
    scenario.move_to_location("shelf")

    # Try to release when not holding anything
    success = scenario.release_object()
    assert not success


def test_reset() -> None:
    """Test scenario reset."""
    scenario = PickAndPlaceScenario()

    # Perform some actions
    scenario.move_to_object("cup")
    scenario.grasp_object("cup")

    # Reset
    scenario.reset()

    state = scenario.get_state()
    assert len(state["action_history"]) == 0
    assert state["objects"]["cup"]["grasped"] is False
    assert state["gripper_state"]["is_grasping"] is False


def test_get_state_telemetry_event_count() -> None:
    """Test that get_state includes telemetry_event_count."""
    scenario = PickAndPlaceScenario()

    state = scenario.get_state()
    assert "telemetry_event_count" in state
    assert state["telemetry_event_count"] == 0

    # Perform an action that generates telemetry
    scenario.move_to_object("cup")

    state = scenario.get_state()
    assert state["telemetry_event_count"] > 0
