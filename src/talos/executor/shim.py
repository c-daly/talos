"""Minimal executor shim for applying plan steps to Neo4j.

This module simulates the Talos action feedback loop by consuming plan nodes
and marking state changes (e.g., grasp/release) in Neo4j.
"""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from neo4j import GraphDatabase, Driver, Session


class ActionType(str, Enum):
    """Types of actions that can be executed."""

    GRASP = "grasp"
    RELEASE = "release"
    MOVE_TO = "move_to"


class PlanNode(BaseModel):
    """Represents a single step in a plan."""

    node_id: str = Field(..., description="Unique identifier for the plan node")
    action_type: ActionType = Field(..., description="Type of action to execute")
    target: str = Field(..., description="Target object or location")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Additional action parameters"
    )


class ExecutorShim:
    """Minimal executor shim for applying plan steps to Neo4j.

    This class provides a simple interface to consume plan nodes and apply
    their state changes to a Neo4j database, simulating Talos action feedback.
    """

    def __init__(self, uri: str, username: str, password: str) -> None:
        """Initialize the executor shim.

        Args:
            uri: Neo4j connection URI (e.g., 'bolt://localhost:7687')
            username: Neo4j username
            password: Neo4j password
        """
        self.driver: Driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self) -> None:
        """Close the Neo4j driver connection."""
        self.driver.close()

    def __enter__(self) -> "ExecutorShim":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

    def execute_plan_node(self, plan_node: PlanNode) -> Dict[str, Any]:
        """Execute a single plan node and update Neo4j state.

        Args:
            plan_node: The plan node to execute

        Returns:
            Dictionary containing execution results and updated state
        """
        with self.driver.session() as session:
            if plan_node.action_type == ActionType.GRASP:
                return self._execute_grasp(session, plan_node)
            elif plan_node.action_type == ActionType.RELEASE:
                return self._execute_release(session, plan_node)
            elif plan_node.action_type == ActionType.MOVE_TO:
                return self._execute_move_to(session, plan_node)
            else:
                raise ValueError(f"Unknown action type: {plan_node.action_type}")

    def _execute_grasp(self, session: Session, plan_node: PlanNode) -> Dict[str, Any]:
        """Execute a grasp action.

        Args:
            session: Neo4j session
            plan_node: The plan node containing grasp details

        Returns:
            Execution results
        """
        # Create or update the object node
        query = """
        MERGE (obj:Object {name: $target})
        SET obj.grasped = true,
            obj.last_action = $action_type,
            obj.last_action_node = $node_id,
            obj.updated_at = datetime()
        RETURN obj
        """
        result = session.run(
            query,
            target=plan_node.target,
            action_type=plan_node.action_type.value,
            node_id=plan_node.node_id,
        )
        result.single()

        return {
            "success": True,
            "action": "grasp",
            "target": plan_node.target,
            "node_id": plan_node.node_id,
            "state": {
                "grasped": True,
                "object_name": plan_node.target,
            },
        }

    def _execute_release(self, session: Session, plan_node: PlanNode) -> Dict[str, Any]:
        """Execute a release action.

        Args:
            session: Neo4j session
            plan_node: The plan node containing release details

        Returns:
            Execution results
        """
        # Update the object node
        query = """
        MATCH (obj:Object {name: $target})
        SET obj.grasped = false,
            obj.last_action = $action_type,
            obj.last_action_node = $node_id,
            obj.updated_at = datetime()
        RETURN obj
        """
        result = session.run(
            query,
            target=plan_node.target,
            action_type=plan_node.action_type.value,
            node_id=plan_node.node_id,
        )
        record = result.single()

        # If no object was found, create it with released state
        if not record:
            query_create = """
            MERGE (obj:Object {name: $target})
            SET obj.grasped = false,
                obj.last_action = $action_type,
                obj.last_action_node = $node_id,
                obj.updated_at = datetime()
            RETURN obj
            """
            result = session.run(
                query_create,
                target=plan_node.target,
                action_type=plan_node.action_type.value,
                node_id=plan_node.node_id,
            )

        return {
            "success": True,
            "action": "release",
            "target": plan_node.target,
            "node_id": plan_node.node_id,
            "state": {
                "grasped": False,
                "object_name": plan_node.target,
            },
        }

    def _execute_move_to(self, session: Session, plan_node: PlanNode) -> Dict[str, Any]:
        """Execute a move_to action.

        Args:
            session: Neo4j session
            plan_node: The plan node containing move details

        Returns:
            Execution results
        """
        # Get position from parameters if available
        position = plan_node.parameters.get("position", None)

        # Create or update the location node and create relationship
        query = """
        MERGE (loc:Location {name: $target})
        SET loc.last_action = $action_type,
            loc.last_action_node = $node_id,
            loc.updated_at = datetime()
        WITH loc
        MERGE (state:RobotState {id: 'current'})
        MERGE (state)-[r:AT_LOCATION]->(loc)
        SET r.updated_at = datetime()
        RETURN loc, state
        """
        params: Dict[str, Any] = {
            "target": plan_node.target,
            "action_type": plan_node.action_type.value,
            "node_id": plan_node.node_id,
        }

        if position is not None:
            query = """
            MERGE (loc:Location {name: $target})
            SET loc.position = $position,
                loc.last_action = $action_type,
                loc.last_action_node = $node_id,
                loc.updated_at = datetime()
            WITH loc
            MERGE (state:RobotState {id: 'current'})
            MERGE (state)-[r:AT_LOCATION]->(loc)
            SET r.updated_at = datetime()
            RETURN loc, state
            """
            params["position"] = position

        result = session.run(query, **params)
        result.single()

        return {
            "success": True,
            "action": "move_to",
            "target": plan_node.target,
            "node_id": plan_node.node_id,
            "state": {
                "location": plan_node.target,
                "position": position,
            },
        }

    def get_object_state(self, object_name: str) -> Optional[Dict[str, Any]]:
        """Get the current state of an object from Neo4j.

        Args:
            object_name: Name of the object

        Returns:
            Dictionary containing object state, or None if not found
        """
        with self.driver.session() as session:
            query = """
            MATCH (obj:Object {name: $object_name})
            RETURN obj.name as name,
                   obj.grasped as grasped,
                   obj.last_action as last_action,
                   obj.last_action_node as last_action_node
            """
            result = session.run(query, object_name=object_name)
            record = result.single()

            if record:
                return {
                    "name": record["name"],
                    "grasped": record["grasped"],
                    "last_action": record["last_action"],
                    "last_action_node": record["last_action_node"],
                }
            return None

    def get_robot_location(self) -> Optional[str]:
        """Get the current robot location from Neo4j.

        Returns:
            Current location name, or None if not found
        """
        with self.driver.session() as session:
            query = """
            MATCH (state:RobotState {id: 'current'})-[:AT_LOCATION]->(loc:Location)
            RETURN loc.name as location
            """
            result = session.run(query)
            record = result.single()

            if record:
                location = record["location"]
                if isinstance(location, str):
                    return location
            return None

    def clear_database(self) -> None:
        """Clear all nodes and relationships from the database.

        This is useful for testing and resetting state.
        """
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
