"""Example: Using telemetry to track actuator operations."""

from talos.actuators import SimulatedMotor, SimulatedGripper
from talos.telemetry import TelemetryRecorder, EventType


def main() -> None:
    """Demonstrate telemetry usage with actuators."""
    print("Talos Telemetry Example\n" + "=" * 50)

    # Create a shared telemetry recorder
    telemetry = TelemetryRecorder(max_events=100)

    # Create actuators with shared telemetry
    motor = SimulatedMotor(name="arm_joint_1", telemetry=telemetry)
    gripper = SimulatedGripper(name="gripper", telemetry=telemetry)

    print("\nCreated actuators with shared telemetry recorder")

    # Perform some operations
    print("\nPerforming actuator operations...")
    motor.set_position(1.57)  # 90 degrees
    motor.set_velocity(0.5)
    motor.set_position(3.0)  # Will be clamped to max

    gripper.close()
    gripper.grasp("cup")
    gripper.release()

    # Display telemetry statistics
    print(f"\nTotal telemetry events recorded: {telemetry.get_event_count()}")

    # Show motor events
    motor_events = telemetry.get_events(actuator_name="arm_joint_1")
    print(f"\nMotor events: {len(motor_events)}")
    for event in motor_events:
        print(f"  - {event.event_type.value}: {event.data}")

    # Show gripper events
    gripper_events = telemetry.get_events(actuator_name="gripper")
    print(f"\nGripper events: {len(gripper_events)}")
    for event in gripper_events:
        print(f"  - {event.event_type.value}: {event.data}")

    # Filter by event type
    position_events = telemetry.get_events(event_type=EventType.POSITION_SET)
    print(f"\nAll position set events: {len(position_events)}")
    for event in position_events:
        data = event.data
        print(
            f"  - {event.actuator_name}: "
            f"requested={data['requested_position']:.2f}, "
            f"clamped={data['clamped_position']:.2f}"
        )

    # Export telemetry data
    print("\nExporting telemetry to dictionary format...")
    telemetry_export = telemetry.to_dict()
    print(f"Exported {len(telemetry_export)} events")

    # Show last 3 events
    print("\nLast 3 events:")
    for event_dict in telemetry_export[-3:]:
        print(f"  - {event_dict['timestamp']}: {event_dict['event_type']}")
        print(f"    Actuator: {event_dict['actuator_name']}")
        print(f"    Data: {event_dict['data']}")

    # Demonstrate telemetry clearing
    print(f"\nClearing telemetry (had {telemetry.get_event_count()} events)...")
    telemetry.clear()
    print(f"Events after clear: {telemetry.get_event_count()}")


if __name__ == "__main__":
    main()
