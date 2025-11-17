"""Example: Using simulated actuators."""

from talos.actuators import SimulatedMotor, SimulatedGripper


def main() -> None:
    """Demonstrate actuator usage."""
    print("Talos Actuators Example\n" + "=" * 50)

    # Create actuators
    motor = SimulatedMotor(name="arm_joint_1")
    gripper = SimulatedGripper()

    print("\nCreated actuators:")
    print(f"  Motor: {motor.get_info()}")
    print(f"  Gripper: {gripper.get_info()}")

    # Control motor
    print("\nControlling motor...")
    motor.set_position(1.57)  # 90 degrees
    print("  Set position to 1.57 rad")
    print(f"  Current state: {motor.get_state()}")

    motor.set_velocity(0.5)
    print("  Set velocity to 0.5 rad/s")
    print(f"  Current state: {motor.get_state()}")

    # Control gripper
    print("\nControlling gripper...")
    gripper.close()
    print("  Closed gripper")
    print(f"  Current state: {gripper.get_state()}")

    success = gripper.grasp("cup")
    print(f"  Attempted to grasp cup: {'Success' if success else 'Failed'}")
    print(f"  Current state: {gripper.get_state()}")

    gripper.release()
    print("  Released object")
    print(f"  Current state: {gripper.get_state()}")


if __name__ == "__main__":
    main()
