"""M4 test: Simulate executor/Talos loop.

This test validates the executor shim that applies plan steps to Neo4j,
representing Talos action feedback without requiring hardware.
"""

from typing import Any, Dict, List, Optional
from unittest.mock import patch
import pytest

from talos.executor import ExecutorShim, PlanNode, ActionType
from talos.scenarios.pick_and_place import PickAndPlaceScenario


class MockNeo4jDriver:
    """Mock Neo4j driver for testing without a real database."""

    def __init__(self) -> None:
        """Initialize mock driver with in-memory storage."""
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.relationships: List[Dict[str, Any]] = []
        self.closed = False

    def close(self) -> None:
        """Mock close method."""
        self.closed = True

    def session(self) -> "MockNeo4jSession":
        """Create a mock session."""
        return MockNeo4jSession(self)


class MockNeo4jSession:
    """Mock Neo4j session for testing."""

    def __init__(self, driver: MockNeo4jDriver) -> None:
        """Initialize mock session."""
        self.driver = driver

    def __enter__(self) -> "MockNeo4jSession":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        pass

    def run(self, query: str, **params: Any) -> "MockNeo4jResult":
        """Execute a mock query."""
        return MockNeo4jResult(self.driver, query, params)


class MockNeo4jResult:
    """Mock Neo4j result."""

    def __init__(
        self, driver: MockNeo4jDriver, query: str, params: Dict[str, Any]
    ) -> None:
        """Initialize mock result."""
        self.driver = driver
        self.query = query
        self.params = params
        self._execute_query()

    def _execute_query(self) -> None:
        """Execute the query against mock storage."""
        if "MERGE (obj:Object" in self.query:
            # Handle object operations
            target = self.params.get("target")
            if target:
                node_key = f"Object:{target}"
                if node_key not in self.driver.nodes:
                    self.driver.nodes[node_key] = {
                        "name": target,
                        "grasped": False,
                    }
                # Update node properties
                if "grasped = true" in self.query:
                    self.driver.nodes[node_key]["grasped"] = True
                elif "grasped = false" in self.query:
                    self.driver.nodes[node_key]["grasped"] = False
                if "last_action" in self.query:
                    self.driver.nodes[node_key]["last_action"] = self.params.get(
                        "action_type"
                    )
                    self.driver.nodes[node_key]["last_action_node"] = self.params.get(
                        "node_id"
                    )

        elif "MATCH (obj:Object" in self.query:
            # Handle match operations for queries (get_object_state) or updates
            target = self.params.get("object_name") or self.params.get("target")
            if target:
                node_key = f"Object:{target}"
                if node_key in self.driver.nodes:
                    if "grasped = false" in self.query:
                        self.driver.nodes[node_key]["grasped"] = False
                    if "last_action" in self.query and "SET" in self.query:
                        self.driver.nodes[node_key]["last_action"] = self.params.get(
                            "action_type"
                        )
                        self.driver.nodes[node_key]["last_action_node"] = (
                            self.params.get("node_id")
                        )

        elif "MERGE (loc:Location" in self.query:
            # Handle location operations
            target = self.params.get("target")
            if target:
                node_key = f"Location:{target}"
                if node_key not in self.driver.nodes:
                    self.driver.nodes[node_key] = {"name": target}
                # Update node properties
                if "last_action" in self.query:
                    self.driver.nodes[node_key]["last_action"] = self.params.get(
                        "action_type"
                    )
                    self.driver.nodes[node_key]["last_action_node"] = self.params.get(
                        "node_id"
                    )
                if "position" in self.params:
                    self.driver.nodes[node_key]["position"] = self.params.get(
                        "position"
                    )
                # Create robot state relationship
                state_key = "RobotState:current"
                if state_key not in self.driver.nodes:
                    self.driver.nodes[state_key] = {"id": "current"}
                # Remove any existing AT_LOCATION relationships for this state
                self.driver.relationships = [
                    rel
                    for rel in self.driver.relationships
                    if not (rel["from"] == state_key and rel["type"] == "AT_LOCATION")
                ]
                # Store new relationship
                self.driver.relationships.append(
                    {"from": state_key, "to": node_key, "type": "AT_LOCATION"}
                )

        elif "MATCH (state:RobotState" in self.query and "AT_LOCATION" in self.query:
            # Handle robot location query
            pass  # Will be handled in single()

        elif "MATCH (n) DETACH DELETE n" in self.query:
            # Clear all data
            self.driver.nodes.clear()
            self.driver.relationships.clear()

    def single(self) -> Optional["MockNeo4jRecord"]:
        """Return a single record."""
        if "MATCH (obj:Object" in self.query:
            target = self.params.get("object_name")
            if target:
                node_key = f"Object:{target}"
                if node_key in self.driver.nodes:
                    return MockNeo4jRecord(self.driver.nodes[node_key])
            return None
        elif "MATCH (state:RobotState" in self.query:
            # Find the current location relationship
            state_key = "RobotState:current"
            for rel in self.driver.relationships:
                if rel["from"] == state_key and rel["type"] == "AT_LOCATION":
                    loc_key = rel["to"]
                    if loc_key in self.driver.nodes:
                        return MockNeo4jRecord(
                            {"location": self.driver.nodes[loc_key]["name"]}
                        )
            return None
        elif "RETURN obj" in self.query or "RETURN loc" in self.query:
            # Return the modified node
            return MockNeo4jRecord({})
        return MockNeo4jRecord({})


class MockNeo4jRecord:
    """Mock Neo4j record."""

    def __init__(self, data: Dict[str, Any]) -> None:
        """Initialize mock record."""
        self.data = data

    def __getitem__(self, key: str) -> Any:
        """Get item from record."""
        return self.data.get(key)


@pytest.fixture
def mock_neo4j_driver() -> MockNeo4jDriver:
    """Provide a mock Neo4j driver for testing."""
    return MockNeo4jDriver()


@pytest.fixture
def executor_shim(mock_neo4j_driver: MockNeo4jDriver) -> ExecutorShim:
    """Provide an executor shim with mock Neo4j driver."""
    with patch(
        "talos.executor.shim.GraphDatabase.driver", return_value=mock_neo4j_driver
    ):
        shim = ExecutorShim("bolt://localhost:7687", "neo4j", "password")
        yield shim
        shim.close()


def test_executor_shim_initialization(executor_shim: ExecutorShim) -> None:
    """Test executor shim initialization."""
    assert executor_shim is not None
    assert executor_shim.driver is not None


def test_executor_shim_context_manager(mock_neo4j_driver: MockNeo4jDriver) -> None:
    """Test executor shim as context manager."""
    with patch(
        "talos.executor.shim.GraphDatabase.driver", return_value=mock_neo4j_driver
    ):
        with ExecutorShim("bolt://localhost:7687", "neo4j", "password") as shim:
            assert shim is not None
        assert mock_neo4j_driver.closed


def test_execute_grasp_plan_node(executor_shim: ExecutorShim) -> None:
    """Test executing a grasp plan node."""
    plan_node = PlanNode(node_id="plan_001", action_type=ActionType.GRASP, target="cup")

    result = executor_shim.execute_plan_node(plan_node)

    assert result["success"] is True
    assert result["action"] == "grasp"
    assert result["target"] == "cup"
    assert result["node_id"] == "plan_001"
    assert result["state"]["grasped"] is True
    assert result["state"]["object_name"] == "cup"


def test_execute_release_plan_node(executor_shim: ExecutorShim) -> None:
    """Test executing a release plan node."""
    # First grasp an object
    grasp_node = PlanNode(
        node_id="plan_001", action_type=ActionType.GRASP, target="cup"
    )
    executor_shim.execute_plan_node(grasp_node)

    # Then release it
    release_node = PlanNode(
        node_id="plan_002", action_type=ActionType.RELEASE, target="cup"
    )
    result = executor_shim.execute_plan_node(release_node)

    assert result["success"] is True
    assert result["action"] == "release"
    assert result["target"] == "cup"
    assert result["node_id"] == "plan_002"
    assert result["state"]["grasped"] is False


def test_execute_move_to_plan_node(executor_shim: ExecutorShim) -> None:
    """Test executing a move_to plan node."""
    plan_node = PlanNode(
        node_id="plan_003",
        action_type=ActionType.MOVE_TO,
        target="table",
        parameters={"position": [0.4, 0.0, 0.0]},
    )

    result = executor_shim.execute_plan_node(plan_node)

    assert result["success"] is True
    assert result["action"] == "move_to"
    assert result["target"] == "table"
    assert result["node_id"] == "plan_003"
    assert result["state"]["location"] == "table"
    assert result["state"]["position"] == [0.4, 0.0, 0.0]


def test_get_object_state(executor_shim: ExecutorShim) -> None:
    """Test retrieving object state from Neo4j."""
    # Create an object with grasp action
    plan_node = PlanNode(node_id="plan_001", action_type=ActionType.GRASP, target="cup")
    executor_shim.execute_plan_node(plan_node)

    # Get the object state
    state = executor_shim.get_object_state("cup")

    assert state is not None
    assert state["name"] == "cup"
    assert state["grasped"] is True
    assert state["last_action"] == "grasp"
    assert state["last_action_node"] == "plan_001"


def test_get_object_state_not_found(executor_shim: ExecutorShim) -> None:
    """Test retrieving state of non-existent object."""
    state = executor_shim.get_object_state("nonexistent")
    assert state is None


def test_get_robot_location(executor_shim: ExecutorShim) -> None:
    """Test retrieving robot location from Neo4j."""
    # Move robot to a location
    plan_node = PlanNode(
        node_id="plan_001", action_type=ActionType.MOVE_TO, target="shelf"
    )
    executor_shim.execute_plan_node(plan_node)

    # Get the robot location
    location = executor_shim.get_robot_location()

    assert location == "shelf"


def test_get_robot_location_not_set(executor_shim: ExecutorShim) -> None:
    """Test retrieving robot location when not set."""
    location = executor_shim.get_robot_location()
    assert location is None


def test_clear_database(executor_shim: ExecutorShim) -> None:
    """Test clearing the database."""
    # Add some data
    plan_node = PlanNode(node_id="plan_001", action_type=ActionType.GRASP, target="cup")
    executor_shim.execute_plan_node(plan_node)

    # Clear database
    executor_shim.clear_database()

    # Verify data is cleared
    state = executor_shim.get_object_state("cup")
    assert state is None


def test_m4_pick_and_place_simulation(executor_shim: ExecutorShim) -> None:
    """M4 Test: Simulate complete pick and place with executor/Talos loop.

    This test simulates the full executor/Talos loop:
    1. Create a simulated Talos scenario
    2. Generate plan nodes from scenario actions
    3. Apply plan nodes via executor shim to Neo4j
    4. Assert resulting state and relationships in Neo4j
    """
    # Create Talos pick and place scenario
    scenario = PickAndPlaceScenario()

    # Step 1: Move to object location
    scenario.move_to_object("cup")
    move_node = PlanNode(
        node_id="m4_plan_001",
        action_type=ActionType.MOVE_TO,
        target="cup_location",
        parameters={"position": scenario.objects["cup"]["position"].tolist()},
    )
    move_result = executor_shim.execute_plan_node(move_node)
    assert move_result["success"] is True
    assert executor_shim.get_robot_location() == "cup_location"

    # Step 2: Grasp object
    scenario.grasp_object("cup")
    grasp_node = PlanNode(
        node_id="m4_plan_002", action_type=ActionType.GRASP, target="cup"
    )
    grasp_result = executor_shim.execute_plan_node(grasp_node)
    assert grasp_result["success"] is True
    cup_state = executor_shim.get_object_state("cup")
    assert cup_state is not None
    assert cup_state["grasped"] is True
    assert cup_state["last_action"] == "grasp"

    # Step 3: Move to target location
    scenario.move_to_location("shelf")
    move_to_shelf_node = PlanNode(
        node_id="m4_plan_003",
        action_type=ActionType.MOVE_TO,
        target="shelf",
        parameters={"position": scenario.locations["shelf"].tolist()},
    )
    move_to_shelf_result = executor_shim.execute_plan_node(move_to_shelf_node)
    assert move_to_shelf_result["success"] is True
    assert executor_shim.get_robot_location() == "shelf"

    # Step 4: Release object
    scenario.release_object()
    release_node = PlanNode(
        node_id="m4_plan_004", action_type=ActionType.RELEASE, target="cup"
    )
    release_result = executor_shim.execute_plan_node(release_node)
    assert release_result["success"] is True
    cup_state_after_release = executor_shim.get_object_state("cup")
    assert cup_state_after_release is not None
    assert cup_state_after_release["grasped"] is False
    assert cup_state_after_release["last_action"] == "release"

    # Verify complete state
    assert scenario.gripper.get_grasped_object() is None
    assert scenario.objects["cup"]["grasped"] is False


def test_m4_multiple_objects(executor_shim: ExecutorShim) -> None:
    """M4 Test: Handle multiple objects in sequence."""
    # Grasp first object
    grasp_cup = PlanNode(
        node_id="m4_multi_001", action_type=ActionType.GRASP, target="cup"
    )
    executor_shim.execute_plan_node(grasp_cup)

    # Release first object
    release_cup = PlanNode(
        node_id="m4_multi_002", action_type=ActionType.RELEASE, target="cup"
    )
    executor_shim.execute_plan_node(release_cup)

    # Grasp second object
    grasp_block = PlanNode(
        node_id="m4_multi_003", action_type=ActionType.GRASP, target="block"
    )
    executor_shim.execute_plan_node(grasp_block)

    # Verify states
    cup_state = executor_shim.get_object_state("cup")
    assert cup_state is not None
    assert cup_state["grasped"] is False

    block_state = executor_shim.get_object_state("block")
    assert block_state is not None
    assert block_state["grasped"] is True


def test_m4_invalid_action_type() -> None:
    """M4 Test: Handle invalid action type."""
    with patch("talos.executor.shim.GraphDatabase.driver") as mock_driver:
        mock_driver.return_value = MockNeo4jDriver()
        shim = ExecutorShim("bolt://localhost:7687", "neo4j", "password")

        # Create a plan node with an invalid action type by manipulating the object
        plan_node = PlanNode(
            node_id="invalid_001", action_type=ActionType.GRASP, target="cup"
        )
        # Change action type to something invalid
        plan_node.action_type = "invalid_action"  # type: ignore

        with pytest.raises(ValueError, match="Unknown action type"):
            shim.execute_plan_node(plan_node)
