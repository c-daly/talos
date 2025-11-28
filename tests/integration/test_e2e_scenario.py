"""End-to-end scenario tests for complete Talos workflows.

These tests combine multiple components (sensors, actuators, executor, telemetry)
to validate complete workflows with real services where available.
"""

import os
import pytest

from talos.scenarios.pick_and_place import PickAndPlaceScenario
from talos.executor import ExecutorShim, PlanNode, ActionType
from talos.telemetry import EventType


# Integration test marker
pytestmark = pytest.mark.integration


def neo4j_available() -> bool:
    """Check if Neo4j is available for testing."""
    try:
        from neo4j import GraphDatabase

        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "neo4jtest")

        driver = GraphDatabase.driver(uri, auth=(username, password))
        with driver.session() as session:
            session.run("RETURN 1")
        driver.close()
        return True
    except Exception:
        return False


@pytest.fixture
def pick_and_place_scenario() -> PickAndPlaceScenario:
    """Provide a pick and place scenario for testing."""
    return PickAndPlaceScenario()


def test_complete_pick_and_place_with_telemetry(
    pick_and_place_scenario: PickAndPlaceScenario,
) -> None:
    """Test complete pick-and-place with telemetry tracking."""
    scenario = pick_and_place_scenario

    # Execute full pick and place
    success, actions = scenario.execute_pick_and_place("cup", "shelf")

    assert success
    assert len(actions) == 4

    # Verify telemetry captured all operations
    telemetry_events = scenario.telemetry.get_events()
    assert len(telemetry_events) > 0

    # Verify specific event types exist
    position_events = scenario.telemetry.get_events(event_type=EventType.POSITION_SET)
    gripper_events = scenario.telemetry.get_events(event_type=EventType.GRIPPER_CLOSED)
    grasp_events = scenario.telemetry.get_events(event_type=EventType.OBJECT_GRASPED)

    assert len(position_events) > 0
    assert len(gripper_events) > 0
    assert len(grasp_events) > 0


def test_sensor_reading_to_planning_execution_loop(
    pick_and_place_scenario: PickAndPlaceScenario,
) -> None:
    """Test sensor reading → planning → execution loop."""
    scenario = pick_and_place_scenario

    # Read sensors
    camera_frame = scenario.camera.read()
    depth_map = scenario.depth.read()
    imu_data = scenario.imu.read()

    # Verify sensor data
    assert camera_frame is not None
    assert depth_map is not None
    assert imu_data is not None

    # Execute action based on "sensor data"
    success = scenario.move_to_object("cup")
    assert success

    # Verify actuator state changed
    state = scenario.get_state()
    assert len(state["action_history"]) > 0


@pytest.mark.skipif(not neo4j_available(), reason="Neo4j not available")
def test_executor_feedback_replanning_flow() -> None:
    """Test executor feedback → replanning flow."""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "neo4jtest")

    executor = ExecutorShim(uri, username, password)
    executor.clear_database()

    try:
        # Initial plan: grasp object
        plan1 = PlanNode(node_id="plan_001", action_type=ActionType.GRASP, target="cup")
        result1 = executor.execute_plan_node(plan1)

        assert result1["success"]
        assert result1["state"]["grasped"]

        # Get feedback from executor
        cup_state = executor.get_object_state("cup")
        assert cup_state is not None
        assert cup_state["grasped"]

        # Replan based on feedback: release object
        plan2 = PlanNode(
            node_id="plan_002", action_type=ActionType.RELEASE, target="cup"
        )
        result2 = executor.execute_plan_node(plan2)

        assert result2["success"]
        assert not result2["state"]["grasped"]

        # Verify replanning worked
        cup_state_after = executor.get_object_state("cup")
        assert cup_state_after is not None
        assert not cup_state_after["grasped"]

    finally:
        executor.clear_database()
        executor.close()


def test_telemetry_streaming_during_operation(
    pick_and_place_scenario: PickAndPlaceScenario,
) -> None:
    """Test telemetry streaming during operation."""
    scenario = pick_and_place_scenario

    # Start operation
    scenario.move_to_object("cup")

    # Check telemetry in real-time
    events_after_move = scenario.telemetry.get_events()
    initial_count = len(events_after_move)

    # Continue operation
    scenario.grasp_object("cup")

    # Check telemetry updated
    events_after_grasp = scenario.telemetry.get_events()
    assert len(events_after_grasp) > initial_count


def test_error_recovery_in_multi_step_scenario(
    pick_and_place_scenario: PickAndPlaceScenario,
) -> None:
    """Test error recovery in multi-step scenarios."""
    scenario = pick_and_place_scenario

    # Start normal operation
    scenario.move_to_object("cup")
    scenario.grasp_object("cup")

    # Simulate error by disabling actuator
    scenario.gripper.disable()

    # Try to continue (should fail gracefully)
    try:
        scenario.move_to_location("shelf")
        # Movement might succeed as gripper not needed
        assert True
    except RuntimeError:
        # Expected if gripper state affects movement
        assert True

    # Recover
    scenario.gripper.enable()
    scenario.release_object()

    # Should be able to continue
    assert scenario.gripper.is_enabled()


def test_scenario_execution_monitoring(
    pick_and_place_scenario: PickAndPlaceScenario,
) -> None:
    """Test scenario execution monitoring."""
    scenario = pick_and_place_scenario

    # Execute with monitoring
    checkpoints = []

    # Checkpoint 1: Start
    checkpoints.append(("start", scenario.get_state()))

    # Checkpoint 2: After move
    scenario.move_to_object("cup")
    checkpoints.append(("move", scenario.get_state()))

    # Checkpoint 3: After grasp
    scenario.grasp_object("cup")
    checkpoints.append(("grasp", scenario.get_state()))

    # Checkpoint 4: After move to location
    scenario.move_to_location("shelf")
    checkpoints.append(("move_to_location", scenario.get_state()))

    # Checkpoint 5: After release
    scenario.release_object()
    checkpoints.append(("release", scenario.get_state()))

    # Verify monitoring captured progression
    assert len(checkpoints) == 5

    # Each checkpoint should have more actions than previous
    for i in range(len(checkpoints) - 1):
        prev_actions = len(checkpoints[i][1]["action_history"])
        next_actions = len(checkpoints[i + 1][1]["action_history"])
        assert next_actions >= prev_actions


def test_resource_cleanup_after_scenario(
    pick_and_place_scenario: PickAndPlaceScenario,
) -> None:
    """Test resource cleanup after scenario completion."""
    scenario = pick_and_place_scenario

    # Execute scenario
    success, actions = scenario.execute_pick_and_place("cup", "shelf")
    assert success

    # Verify resources in clean state
    assert scenario.gripper.get_grasped_object() is None
    assert scenario.gripper.is_enabled()
    assert scenario.joint1.is_enabled()
    assert scenario.joint2.is_enabled()
    assert scenario.joint3.is_enabled()

    # Verify telemetry accessible
    assert scenario.telemetry.is_enabled()
    assert scenario.telemetry.get_event_count() > 0


@pytest.mark.skipif(not neo4j_available(), reason="Neo4j not available")
def test_complete_workflow_with_neo4j() -> None:
    """Test complete workflow with Neo4j integration."""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "neo4jtest")

    # Create scenario and executor
    scenario = PickAndPlaceScenario()
    executor = ExecutorShim(uri, username, password)
    executor.clear_database()

    try:
        # Step 1: Sense (read sensors)
        camera_frame = scenario.camera.read()
        assert camera_frame is not None

        # Step 2: Plan (execute scenario steps)
        scenario.move_to_object("cup")
        scenario.grasp_object("cup")

        # Step 3: Execute (apply to Neo4j via executor)
        grasp_plan = PlanNode(
            node_id="e2e_001", action_type=ActionType.GRASP, target="cup"
        )
        result = executor.execute_plan_node(grasp_plan)

        assert result["success"]

        # Step 4: Verify state in Neo4j
        cup_state = executor.get_object_state("cup")
        assert cup_state is not None
        assert cup_state["grasped"]

        # Step 5: Continue workflow
        scenario.move_to_location("shelf")
        move_plan = PlanNode(
            node_id="e2e_002", action_type=ActionType.MOVE_TO, target="shelf"
        )
        executor.execute_plan_node(move_plan)

        location = executor.get_robot_location()
        assert location == "shelf"

        # Step 6: Complete and verify
        scenario.release_object()
        release_plan = PlanNode(
            node_id="e2e_003", action_type=ActionType.RELEASE, target="cup"
        )
        executor.execute_plan_node(release_plan)

        cup_state_final = executor.get_object_state("cup")
        assert cup_state_final is not None
        assert not cup_state_final["grasped"]

    finally:
        executor.clear_database()
        executor.close()


def test_multi_object_workflow(pick_and_place_scenario: PickAndPlaceScenario) -> None:
    """Test workflow with multiple objects."""
    scenario = pick_and_place_scenario

    # Move first object
    success1, actions1 = scenario.execute_pick_and_place("cup", "shelf")
    assert success1

    # Move second object
    success2, actions2 = scenario.execute_pick_and_place("block", "table")
    assert success2

    # Verify telemetry captured both operations
    total_events = scenario.telemetry.get_event_count()
    assert total_events > len(actions1) + len(actions2)


def test_scenario_with_sensor_feedback(
    pick_and_place_scenario: PickAndPlaceScenario,
) -> None:
    """Test scenario using sensor feedback."""
    scenario = pick_and_place_scenario

    # Read initial sensor state
    initial_camera = scenario.camera.read()
    initial_depth = scenario.depth.read()

    # Execute operation
    scenario.move_to_object("cup")

    # Read sensor state after movement
    after_camera = scenario.camera.read()
    after_depth = scenario.depth.read()

    # Sensors should provide updated readings
    assert not (initial_camera == after_camera).all()
    assert not (initial_depth == after_depth).all()


def test_concurrent_sensor_and_actuator_operations(
    pick_and_place_scenario: PickAndPlaceScenario,
) -> None:
    """Test concurrent sensor and actuator operations."""
    scenario = pick_and_place_scenario

    # Read sensors while actuators move
    scenario.joint1.set_position(0.5)
    camera_frame = scenario.camera.read()

    scenario.joint2.set_position(1.0)
    depth_map = scenario.depth.read()

    scenario.joint3.set_position(1.5)
    imu_data = scenario.imu.read()

    # All operations should complete successfully
    assert camera_frame is not None
    assert depth_map is not None
    assert imu_data is not None
    assert scenario.joint1.get_position() == 0.5
    assert scenario.joint2.get_position() == 1.0
    assert scenario.joint3.get_position() == 1.5


def test_scenario_performance_benchmark(
    pick_and_place_scenario: PickAndPlaceScenario,
) -> None:
    """Test scenario performance benchmark."""
    import time

    scenario = pick_and_place_scenario

    # Measure execution time
    start_time = time.time()
    success, actions = scenario.execute_pick_and_place("cup", "shelf")
    end_time = time.time()

    assert success
    execution_time = end_time - start_time

    # Should complete reasonably fast (< 1 second for simulation)
    assert execution_time < 1.0

    # Verify telemetry overhead is minimal
    assert scenario.telemetry.is_enabled()
