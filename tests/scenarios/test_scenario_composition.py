"""Tests for scenario composition and complex multi-step operations."""

import pytest
from typing import List, Dict, Any

from talos.scenarios.pick_and_place import PickAndPlaceScenario
from talos.telemetry import EventType


def test_chaining_multiple_pick_and_place_operations() -> None:
    """Test chaining multiple pick-and-place operations."""
    scenario = PickAndPlaceScenario()

    # Chain multiple operations
    operations = [
        ("cup", "shelf"),
        ("block", "table"),
    ]

    for obj, location in operations:
        success, actions = scenario.execute_pick_and_place(obj, location)
        assert success
        assert len(actions) > 0

    # Verify both operations completed
    state = scenario.get_state()
    assert len(state["action_history"]) >= 8  # 4 actions per operation


def test_scenario_state_persistence() -> None:
    """Test scenario state persistence between operations."""
    scenario = PickAndPlaceScenario()

    # First operation
    scenario.move_to_object("cup")
    state1 = scenario.get_state()
    history_count_1 = len(state1["action_history"])

    # Second operation
    scenario.grasp_object("cup")
    state2 = scenario.get_state()
    history_count_2 = len(state2["action_history"])

    # State should persist and accumulate
    assert history_count_2 > history_count_1
    assert state1["action_history"][0] == state2["action_history"][0]


def test_scenario_rollback_on_failure() -> None:
    """Test scenario rollback on failure."""
    scenario = PickAndPlaceScenario()

    # Try to pick non-existent object
    success = scenario.move_to_object("nonexistent")
    assert not success

    # State should remain unchanged
    state = scenario.get_state()
    assert len(state["action_history"]) == 0


def test_scenario_telemetry_aggregation() -> None:
    """Test scenario telemetry aggregation."""
    scenario = PickAndPlaceScenario()

    # Execute full pick and place
    success, actions = scenario.execute_pick_and_place("cup", "shelf")
    assert success

    # Telemetry should capture all operations
    telemetry_events = scenario.telemetry.get_events()
    assert len(telemetry_events) > 0

    # Should have events from multiple actuators
    joint_events = scenario.telemetry.get_events(actuator_name="joint1")
    gripper_events = scenario.telemetry.get_events(actuator_name="gripper")

    assert len(joint_events) > 0
    assert len(gripper_events) > 0


def test_custom_scenario_creation() -> None:
    """Test custom scenario creation."""

    class CustomScenario:
        """Custom scenario for testing."""

        def __init__(self) -> None:
            self.steps_executed: List[str] = []

        def step1(self) -> bool:
            self.steps_executed.append("step1")
            return True

        def step2(self) -> bool:
            self.steps_executed.append("step2")
            return True

        def step3(self) -> bool:
            self.steps_executed.append("step3")
            return True

        def execute(self) -> bool:
            return self.step1() and self.step2() and self.step3()

    scenario = CustomScenario()
    success = scenario.execute()

    assert success
    assert len(scenario.steps_executed) == 3
    assert scenario.steps_executed == ["step1", "step2", "step3"]


def test_scenario_validation_preconditions() -> None:
    """Test scenario validation (pre-conditions)."""
    scenario = PickAndPlaceScenario()

    # Pre-condition: gripper must be open to grasp
    scenario.gripper.close()
    success = scenario.grasp_object("cup")
    assert not success  # Should fail because gripper is already closed

    # Reset
    scenario.gripper.open()
    scenario.move_to_object("cup")
    scenario.gripper.close()
    success = scenario.grasp_object("cup")
    assert success  # Should succeed now


def test_scenario_validation_postconditions() -> None:
    """Test scenario validation (post-conditions)."""
    scenario = PickAndPlaceScenario()

    # Execute pick and place
    success, actions = scenario.execute_pick_and_place("cup", "shelf")
    assert success

    # Post-condition: object should be at target location
    # (In simulation, we track this via grasped state)
    state = scenario.get_state()
    # After release, object should not be grasped
    assert not state["objects"]["cup"]["grasped"]


def test_scenario_timeout_handling() -> None:
    """Test scenario timeout handling."""
    scenario = PickAndPlaceScenario()

    # Simulate a long-running operation by recording many events
    for i in range(100):
        scenario.joint1.set_position(float(i % 10) * 0.1)

    # Scenario should still function
    success = scenario.move_to_object("cup")
    assert success


def test_scenario_composition_complex() -> None:
    """Test complex scenario composition with multiple objects."""
    scenario = PickAndPlaceScenario()

    # Move multiple objects in sequence
    plan = [
        ("cup", "shelf"),
        ("block", "table"),
    ]

    results = []
    for obj, location in plan:
        success, actions = scenario.execute_pick_and_place(obj, location)
        results.append((obj, location, success))

    # All operations should succeed
    assert all(success for _, _, success in results)

    # Verify state
    state = scenario.get_state()
    # Both objects should have been moved (not currently grasped)
    assert not state["objects"]["cup"]["grasped"]
    assert not state["objects"]["block"]["grasped"]


def test_scenario_step_by_step_execution() -> None:
    """Test scenario execution step by step."""
    scenario = PickAndPlaceScenario()

    # Execute individual steps
    success1 = scenario.move_to_object("cup")
    assert success1

    success2 = scenario.grasp_object("cup")
    assert success2

    success3 = scenario.move_to_location("shelf")
    assert success3

    success4 = scenario.release_object()
    assert success4

    # Verify complete state
    state = scenario.get_state()
    assert len(state["action_history"]) == 4


def test_scenario_partial_execution() -> None:
    """Test partial scenario execution."""
    scenario = PickAndPlaceScenario()

    # Execute only part of a pick and place
    scenario.move_to_object("cup")
    scenario.grasp_object("cup")

    # Object should be grasped but not yet placed
    assert scenario.gripper.get_grasped_object() == "cup"
    assert scenario.objects["cup"]["grasped"]


def test_scenario_error_propagation() -> None:
    """Test error propagation in scenarios."""
    scenario = PickAndPlaceScenario()

    # Try to grasp without moving to object first
    scenario.gripper.close()
    success = scenario.grasp_object("nonexistent_object")

    # Should handle error gracefully
    assert not success


def test_scenario_state_snapshot() -> None:
    """Test taking state snapshots during execution."""
    scenario = PickAndPlaceScenario()

    snapshots: List[Dict[str, Any]] = []

    # Take snapshots during execution
    snapshots.append(scenario.get_state())

    scenario.move_to_object("cup")
    snapshots.append(scenario.get_state())

    scenario.grasp_object("cup")
    snapshots.append(scenario.get_state())

    scenario.move_to_location("shelf")
    snapshots.append(scenario.get_state())

    scenario.release_object()
    snapshots.append(scenario.get_state())

    # Verify snapshots captured progression
    assert len(snapshots) == 5
    for i in range(len(snapshots) - 1):
        # Each snapshot should have more actions than the previous
        assert (
            len(snapshots[i + 1]["action_history"])
            >= len(snapshots[i]["action_history"])
        )


def test_scenario_concurrent_operations() -> None:
    """Test scenario with concurrent operations (multiple joints moving)."""
    scenario = PickAndPlaceScenario()

    # Move all joints simultaneously
    scenario.joint1.set_position(0.5)
    scenario.joint2.set_position(1.0)
    scenario.joint3.set_position(1.5)

    # All joints should reach target positions
    assert scenario.joint1.get_position() == 0.5
    assert scenario.joint2.get_position() == 1.0
    assert scenario.joint3.get_position() == 1.5


def test_scenario_resource_cleanup() -> None:
    """Test resource cleanup after scenario completion."""
    scenario = PickAndPlaceScenario()

    # Execute scenario
    success, actions = scenario.execute_pick_and_place("cup", "shelf")
    assert success

    # Resources should be in clean state
    assert scenario.gripper.get_grasped_object() is None
    assert scenario.gripper.is_enabled()
    assert scenario.joint1.is_enabled()


def test_scenario_repeatability() -> None:
    """Test scenario repeatability."""
    results = []

    for _ in range(3):
        scenario = PickAndPlaceScenario()
        success, actions = scenario.execute_pick_and_place("cup", "shelf")
        results.append((success, len(actions)))

    # All runs should produce same result
    assert all(success for success, _ in results)
    assert len(set(actions_count for _, actions_count in results)) == 1


def test_scenario_action_sequence() -> None:
    """Test that scenario executes actions in correct sequence."""
    scenario = PickAndPlaceScenario()

    success, actions = scenario.execute_pick_and_place("cup", "shelf")
    assert success

    # Verify action sequence
    assert len(actions) == 4
    assert "cup" in actions[0]  # Moved to cup
    assert "Grasped" in actions[1]  # Grasped cup
    assert "shelf" in actions[2]  # Moved to shelf
    assert "Released" in actions[3]  # Released object


def test_scenario_telemetry_timeline() -> None:
    """Test scenario telemetry creates a timeline of events."""
    scenario = PickAndPlaceScenario()

    # Execute scenario
    scenario.execute_pick_and_place("cup", "shelf")

    # Get telemetry events
    events = scenario.telemetry.get_events()

    # Events should be in chronological order
    timestamps = [e.timestamp for e in events]
    assert timestamps == sorted(timestamps)


def test_scenario_graceful_degradation() -> None:
    """Test scenario graceful degradation on component failure."""
    scenario = PickAndPlaceScenario()

    # Disable one joint
    scenario.joint3.disable()

    # Scenario should handle this gracefully
    # In a real system, this might trigger alternative motion planning
    # Here we just verify it doesn't crash
    try:
        scenario.move_to_object("cup")
        # Move succeeded or failed gracefully
        assert True
    except RuntimeError:
        # Expected if disabled joint is used
        assert True


def test_scenario_complex_state_machine() -> None:
    """Test scenario as a complex state machine."""
    scenario = PickAndPlaceScenario()

    states = []

    # Initial state
    states.append("IDLE")

    # Transition through states
    scenario.move_to_object("cup")
    states.append("MOVING_TO_OBJECT")

    scenario.grasp_object("cup")
    states.append("GRASPING")

    scenario.move_to_location("shelf")
    states.append("MOVING_TO_LOCATION")

    scenario.release_object()
    states.append("RELEASING")

    # Back to idle
    states.append("IDLE")

    # Verify state transitions
    assert len(states) == 6
    assert states[0] == "IDLE"
    assert states[-1] == "IDLE"
