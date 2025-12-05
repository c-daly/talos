"""Example demonstrating the executor shim for simulating the Talos/Executor loop.

This example shows how to:
1. Create an executor shim
2. Define plan nodes for a pick-and-place operation
3. Execute the plan nodes
4. Query the resulting state from Neo4j

Note: This example requires a running Neo4j instance. For testing without
a real Neo4j instance, see the M4 tests which use a mock driver.
"""

from talos.executor import ExecutorShim, PlanNode, ActionType
from talos.scenarios import PickAndPlaceScenario


def main() -> None:
    """Demonstrate executor shim with a pick-and-place scenario."""
    print("=== Executor Shim Example ===\n")

    # NOTE: This example assumes you have Neo4j running at bolt://localhost:7687
    # with username "neo4j" and password "password"
    # For testing, you can use the mock driver in test_m4_executor_loop.py
    print(
        "Note: This example requires a running Neo4j instance at bolt://localhost:7687"
    )
    print(
        "For testing without Neo4j, see tests/unit/scenarios/test_m4_executor_loop.py\n"
    )

    # Create the executor shim
    # In a real scenario, replace these with your Neo4j credentials
    try:
        with ExecutorShim(
            uri="bolt://localhost:7687", username="neo4j", password="password"
        ) as executor:
            # Clear any existing data
            executor.clear_database()
            print("Cleared Neo4j database\n")

            # Create a simulated Talos scenario
            scenario = PickAndPlaceScenario()
            print("Created pick-and-place scenario\n")

            # Step 1: Move to object location
            print("Step 1: Moving to cup location...")
            scenario.move_to_object("cup")
            move_node = PlanNode(
                node_id="example_001",
                action_type=ActionType.MOVE_TO,
                target="cup_location",
                parameters={"position": scenario.objects["cup"]["position"].tolist()},
            )
            result = executor.execute_plan_node(move_node)
            print(f"  Result: {result['action']} -> {result['target']}")
            print(f"  Robot location: {executor.get_robot_location()}\n")

            # Step 2: Grasp the cup
            print("Step 2: Grasping cup...")
            scenario.grasp_object("cup")
            grasp_node = PlanNode(
                node_id="example_002", action_type=ActionType.GRASP, target="cup"
            )
            result = executor.execute_plan_node(grasp_node)
            print(f"  Result: {result['action']} -> {result['target']}")
            cup_state = executor.get_object_state("cup")
            print(f"  Cup state: {cup_state}\n")

            # Step 3: Move to target location
            print("Step 3: Moving to shelf...")
            scenario.move_to_location("shelf")
            move_shelf_node = PlanNode(
                node_id="example_003",
                action_type=ActionType.MOVE_TO,
                target="shelf",
                parameters={"position": scenario.locations["shelf"].tolist()},
            )
            result = executor.execute_plan_node(move_shelf_node)
            print(f"  Result: {result['action']} -> {result['target']}")
            print(f"  Robot location: {executor.get_robot_location()}\n")

            # Step 4: Release the cup
            print("Step 4: Releasing cup...")
            scenario.release_object()
            release_node = PlanNode(
                node_id="example_004", action_type=ActionType.RELEASE, target="cup"
            )
            result = executor.execute_plan_node(release_node)
            print(f"  Result: {result['action']} -> {result['target']}")
            cup_state = executor.get_object_state("cup")
            print(f"  Cup state: {cup_state}\n")

            print("=== Pick-and-place sequence completed! ===")
            print("\nFinal state:")
            print(f"  Robot location: {executor.get_robot_location()}")
            print(f"  Cup grasped: {cup_state['grasped'] if cup_state else 'N/A'}")
            print(
                f"  Cup last action: {cup_state['last_action'] if cup_state else 'N/A'}"
            )

    except Exception as e:
        print(f"\nError: {e}")
        print(
            "\nMake sure Neo4j is running at bolt://localhost:7687 with the correct credentials."
        )
        print("Or run the tests to see the example with a mock Neo4j driver:")
        print("  pytest tests/unit/scenarios/test_m4_executor_loop.py -v")


if __name__ == "__main__":
    main()
