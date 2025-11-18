"""Example: Pick and place scenario."""

from talos.scenarios import PickAndPlaceScenario
from talos.telemetry import EventType


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
    print(f"  Telemetry events: {state['telemetry_event_count']}")

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
    print(f"  Total telemetry events: {state['telemetry_event_count']}")

    # Show telemetry summary
    print("\nTelemetry Summary:")
    print("=" * 50)

    # Count events by type
    position_events = scenario.telemetry.get_events(event_type=EventType.POSITION_SET)
    grasp_events = scenario.telemetry.get_events(event_type=EventType.OBJECT_GRASPED)
    release_events = scenario.telemetry.get_events(event_type=EventType.OBJECT_RELEASED)

    print(f"  Motor position changes: {len(position_events)}")
    print(f"  Object grasps: {len(grasp_events)}")
    print(f"  Object releases: {len(release_events)}")

    # Show gripper-specific events
    gripper_events = scenario.telemetry.get_events(actuator_name="gripper")
    print(f"\n  Gripper operations: {len(gripper_events)}")
    for event in gripper_events:
        print(f"    - {event.event_type.value}: {event.data}")

    # Reset and try another object
    print("\n" + "=" * 50)
    print("Resetting scenario...")
    scenario.reset()

    print(f"Events after reset: {scenario.telemetry.get_event_count()}")

    print("\nExecuting pick and place: block -> table")
    success, actions = scenario.execute_pick_and_place("block", "table")

    print(f"\nResult: {'Success' if success else 'Failed'}")
    print("\nActions performed:")
    for i, action in enumerate(actions, 1):
        print(f"  {i}. {action}")

    state = scenario.get_state()
    print(f"\nFinal telemetry events: {state['telemetry_event_count']}")


if __name__ == "__main__":
    main()
