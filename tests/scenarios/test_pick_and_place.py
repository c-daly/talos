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
