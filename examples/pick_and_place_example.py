"""Example: Pick and place scenario."""

from talos.scenarios import PickAndPlaceScenario


def main() -> None:
    """Demonstrate pick and place scenario."""
    print("Talos Pick and Place Scenario\n" + "=" * 50)

    # Create scenario
    scenario = PickAndPlaceScenario()

    print("\nInitial state:")
    state = scenario.get_state()
    print(f"  End effector position: {state['end_effector_position']}")
    print(f"  Objects: {list(state['objects'].keys())}")
    print(f"  Locations: {list(state['locations'].keys())}")

    # Execute pick and place
    print("\nExecuting pick and place: cup -> shelf")
    success, actions = scenario.execute_pick_and_place("cup", "shelf")

    print(f"\nResult: {'Success' if success else 'Failed'}")
    print("\nActions performed:")
    for i, action in enumerate(actions, 1):
        print(f"  {i}. {action}")

    # Show final state
    print("\nFinal state:")
    state = scenario.get_state()
    print(f"  Cup position: {state['objects']['cup']['position']}")
    print(f"  Cup grasped: {state['objects']['cup']['grasped']}")
    print(f"  Gripper state: {state['gripper_state']}")

    # Reset and try another object
    print("\n" + "=" * 50)
    print("Resetting scenario...")
    scenario.reset()

    print("\nExecuting pick and place: block -> table")
    success, actions = scenario.execute_pick_and_place("block", "table")

    print(f"\nResult: {'Success' if success else 'Failed'}")
    print("\nActions performed:")
    for i, action in enumerate(actions, 1):
        print(f"  {i}. {action}")


if __name__ == "__main__":
    main()
