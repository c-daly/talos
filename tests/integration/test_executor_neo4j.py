"""Integration tests for ExecutorShim with real Neo4j instance.

These tests require a running Neo4j instance and are designed to skip gracefully
when Neo4j is not available.
"""

from typing import Generator
import pytest
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

from logos_config.ports import get_repo_ports
from talos.env import get_neo4j_config
from talos.executor import ExecutorShim, PlanNode, ActionType


# Integration test marker
pytestmark = pytest.mark.integration

TALOS_PORTS = get_repo_ports("talos")


def neo4j_available() -> bool:
    """Check if Neo4j is available for testing."""
    config = get_neo4j_config()

    try:
        driver = GraphDatabase.driver(
            config["uri"], auth=(config["user"], config["password"])
        )
        with driver.session() as session:
            session.run("RETURN 1")
        driver.close()
        return True
    except (ServiceUnavailable, AuthError, Exception):
        return False


@pytest.fixture(scope="module")
def neo4j_config() -> dict[str, str]:
    """Get Neo4j connection configuration."""
    return get_neo4j_config()


@pytest.fixture(scope="module")
def neo4j_uri(neo4j_config: dict[str, str]) -> str:
    """Get Neo4j URI from configuration."""
    return neo4j_config["uri"]


@pytest.fixture(scope="module")
def neo4j_username(neo4j_config: dict[str, str]) -> str:
    """Get Neo4j username from configuration."""
    return neo4j_config["user"]


@pytest.fixture(scope="module")
def neo4j_password(neo4j_config: dict[str, str]) -> str:
    """Get Neo4j password from configuration."""
    return neo4j_config["password"]


@pytest.fixture
def executor(
    neo4j_uri: str, neo4j_username: str, neo4j_password: str
) -> Generator[ExecutorShim, None, None]:
    """Provide an executor shim connected to real Neo4j."""
    if not neo4j_available():
        pytest.skip("Neo4j not available")

    shim = ExecutorShim(neo4j_uri, neo4j_username, neo4j_password)
    # Clear database before test
    shim.clear_database()
    yield shim
    # Clean up after test
    shim.clear_database()
    shim.close()


@pytest.mark.skipif(not neo4j_available(), reason="Neo4j not available")
def test_neo4j_connection(executor: ExecutorShim) -> None:
    """Test that we can connect to Neo4j."""
    assert executor.driver is not None


@pytest.mark.skipif(not neo4j_available(), reason="Neo4j not available")
def test_executor_creates_object_node(executor: ExecutorShim) -> None:
    """Test that executor creates object nodes in Neo4j."""
    plan_node = PlanNode(node_id="test_001", action_type=ActionType.GRASP, target="cup")

    result = executor.execute_plan_node(plan_node)

    assert result["success"] is True
    assert result["action"] == "grasp"

    # Verify object exists in Neo4j
    state = executor.get_object_state("cup")
    assert state is not None
    assert state["name"] == "cup"
    assert state["grasped"] is True


@pytest.mark.skipif(not neo4j_available(), reason="Neo4j not available")
def test_executor_updates_object_state(executor: ExecutorShim) -> None:
    """Test that executor updates object state in Neo4j."""
    # First grasp
    grasp_node = PlanNode(
        node_id="test_002", action_type=ActionType.GRASP, target="block"
    )
    executor.execute_plan_node(grasp_node)

    # Then release
    release_node = PlanNode(
        node_id="test_003", action_type=ActionType.RELEASE, target="block"
    )
    executor.execute_plan_node(release_node)

    # Verify final state
    state = executor.get_object_state("block")
    assert state is not None
    assert state["grasped"] is False
    assert state["last_action"] == "release"
    assert state["last_action_node"] == "test_003"


@pytest.mark.skipif(not neo4j_available(), reason="Neo4j not available")
def test_executor_creates_location_node(executor: ExecutorShim) -> None:
    """Test that executor creates location nodes in Neo4j."""
    plan_node = PlanNode(
        node_id="test_004",
        action_type=ActionType.MOVE_TO,
        target="shelf",
        parameters={"position": [0.3, 0.2, 0.3]},
    )

    result = executor.execute_plan_node(plan_node)

    assert result["success"] is True
    assert result["action"] == "move_to"

    # Verify robot location
    location = executor.get_robot_location()
    assert location == "shelf"


@pytest.mark.skipif(not neo4j_available(), reason="Neo4j not available")
def test_executor_updates_robot_location(executor: ExecutorShim) -> None:
    """Test that executor updates robot location in Neo4j."""
    # Move to first location
    move1 = PlanNode(node_id="test_005", action_type=ActionType.MOVE_TO, target="table")
    executor.execute_plan_node(move1)
    assert executor.get_robot_location() == "table"

    # Move to second location
    move2 = PlanNode(node_id="test_006", action_type=ActionType.MOVE_TO, target="shelf")
    executor.execute_plan_node(move2)
    assert executor.get_robot_location() == "shelf"


@pytest.mark.skipif(not neo4j_available(), reason="Neo4j not available")
def test_executor_action_history_persists(executor: ExecutorShim) -> None:
    """Test that action history persists in Neo4j."""
    # Execute sequence of actions
    actions = [
        PlanNode(node_id="seq_001", action_type=ActionType.GRASP, target="cup"),
        PlanNode(
            node_id="seq_002", action_type=ActionType.MOVE_TO, target="destination"
        ),
        PlanNode(node_id="seq_003", action_type=ActionType.RELEASE, target="cup"),
    ]

    for action in actions:
        executor.execute_plan_node(action)

    # Verify final state preserves history
    cup_state = executor.get_object_state("cup")
    assert cup_state is not None
    assert cup_state["last_action"] == "release"
    assert cup_state["last_action_node"] == "seq_003"

    location = executor.get_robot_location()
    assert location == "destination"


@pytest.mark.skipif(not neo4j_available(), reason="Neo4j not available")
def test_executor_concurrent_actions(executor: ExecutorShim) -> None:
    """Test executor handles multiple objects correctly."""
    # Grasp first object
    grasp_cup = PlanNode(node_id="conc_001", action_type=ActionType.GRASP, target="cup")
    executor.execute_plan_node(grasp_cup)

    # Grasp second object (simulating multi-gripper or sequence)
    grasp_block = PlanNode(
        node_id="conc_002", action_type=ActionType.GRASP, target="block"
    )
    executor.execute_plan_node(grasp_block)

    # Verify both objects have correct state
    cup_state = executor.get_object_state("cup")
    assert cup_state is not None
    assert cup_state["grasped"] is True

    block_state = executor.get_object_state("block")
    assert block_state is not None
    assert block_state["grasped"] is True


@pytest.mark.skipif(not neo4j_available(), reason="Neo4j not available")
def test_executor_neo4j_connection_failure() -> None:
    """Test error handling when Neo4j connection fails."""
    executor = ExecutorShim(
        f"bolt://invalid:{TALOS_PORTS.neo4j_bolt}", "neo4j", "password"
    )
    # Driver is lazy, so we need to actually attempt an operation to trigger connection
    with pytest.raises((ServiceUnavailable, Exception)):
        executor.get_robot_location()


@pytest.mark.skipif(not neo4j_available(), reason="Neo4j not available")
def test_executor_clear_database(executor: ExecutorShim) -> None:
    """Test that clear_database removes all nodes."""
    # Create some data
    executor.execute_plan_node(
        PlanNode(node_id="clear_001", action_type=ActionType.GRASP, target="cup")
    )
    executor.execute_plan_node(
        PlanNode(node_id="clear_002", action_type=ActionType.MOVE_TO, target="shelf")
    )

    # Verify data exists
    assert executor.get_object_state("cup") is not None
    assert executor.get_robot_location() is not None

    # Clear database
    executor.clear_database()

    # Verify data is gone
    assert executor.get_object_state("cup") is None
    assert executor.get_robot_location() is None


@pytest.mark.skipif(not neo4j_available(), reason="Neo4j not available")
def test_executor_position_persistence(executor: ExecutorShim) -> None:
    """Test that location positions persist in Neo4j."""
    position = [0.5, 0.3, 0.2]
    plan_node = PlanNode(
        node_id="pos_001",
        action_type=ActionType.MOVE_TO,
        target="target_location",
        parameters={"position": position},
    )

    result = executor.execute_plan_node(plan_node)

    assert result["state"]["position"] == position
    assert executor.get_robot_location() == "target_location"


@pytest.mark.skipif(not neo4j_available(), reason="Neo4j not available")
def test_executor_complete_pick_and_place(executor: ExecutorShim) -> None:
    """Test complete pick and place scenario with Neo4j."""
    # Move to object
    executor.execute_plan_node(
        PlanNode(
            node_id="pp_001",
            action_type=ActionType.MOVE_TO,
            target="cup_location",
            parameters={"position": [0.1, 0.2, 0.3]},
        )
    )
    assert executor.get_robot_location() == "cup_location"

    # Grasp object
    executor.execute_plan_node(
        PlanNode(node_id="pp_002", action_type=ActionType.GRASP, target="cup")
    )
    cup_state = executor.get_object_state("cup")
    assert cup_state is not None
    assert cup_state["grasped"] is True

    # Move to destination
    executor.execute_plan_node(
        PlanNode(
            node_id="pp_003",
            action_type=ActionType.MOVE_TO,
            target="shelf",
            parameters={"position": [0.4, 0.5, 0.6]},
        )
    )
    assert executor.get_robot_location() == "shelf"

    # Release object
    executor.execute_plan_node(
        PlanNode(node_id="pp_004", action_type=ActionType.RELEASE, target="cup")
    )
    cup_state = executor.get_object_state("cup")
    assert cup_state is not None
    assert cup_state["grasped"] is False
    assert cup_state["last_action"] == "release"
