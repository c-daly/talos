"""Example: Using Talos mock hardware fixtures in tests.

This example demonstrates how external projects (like Sophia) can use
Talos fixtures for testing robotic scenarios.
"""

# To use Talos fixtures in your tests, add this to your conftest.py:
# pytest_plugins = ["talos.fixtures"]

# Or import directly in your test file (for documentation purposes):
# from talos.fixtures import (
#     mock_camera,
#     mock_pick_and_place,
#     mock_robot_arm,
#     mock_sensor_suite,
# )

# Note: The actual imports are done by pytest when fixtures are used as parameters


def example_test_with_camera(mock_camera):  # noqa: F811
    """Example test using the camera fixture."""
    # The fixture provides a ready-to-use simulated camera
    image = mock_camera.read()

    # Process the image (your custom logic here)
    assert image.shape == (480, 640, 3)
    print(f"Captured image with shape: {image.shape}")


def example_test_pick_and_place(mock_pick_and_place):  # noqa: F811
    """Example test using the complete pick-and-place scenario."""
    scenario = mock_pick_and_place

    # Get initial state
    initial_state = scenario.get_state()
    print(f"Available objects: {list(initial_state['objects'].keys())}")
    print(f"Available locations: {list(initial_state['locations'].keys())}")

    # Execute pick and place operation
    success, actions = scenario.execute_pick_and_place("cup", "shelf")

    assert success, "Pick and place should succeed"
    print(f"Actions performed: {actions}")

    # Access telemetry for analysis
    telemetry_data = scenario.telemetry.to_dict()
    print(f"Total events recorded: {len(telemetry_data['events'])}")


def example_test_robot_coordination(mock_robot_arm):  # noqa: F811
    """Example test for multi-joint robot arm coordination."""
    arm = mock_robot_arm

    # Define a trajectory (sequence of positions)
    trajectory = [
        {"joint1": 0.0, "joint2": 0.0, "joint3": 0.0},  # Home
        {"joint1": 0.5, "joint2": 1.0, "joint3": 0.5},  # Intermediate
        {"joint1": 1.0, "joint2": 1.5, "joint3": 1.0},  # Target
    ]

    # Execute trajectory
    for waypoint in trajectory:
        for joint_name, position in waypoint.items():
            arm[joint_name].set_position(position)

        # Verify positions reached
        for joint_name, expected_pos in waypoint.items():
            actual_pos = arm[joint_name].get_position()
            assert actual_pos == expected_pos

    print("Trajectory execution completed successfully")


def example_test_sensor_fusion(mock_sensor_suite):  # noqa: F811
    """Example test demonstrating sensor fusion."""
    sensors = mock_sensor_suite

    # Read from multiple sensors
    image = sensors["camera"].read()
    depth = sensors["depth"].read()
    acceleration, gyroscope = sensors["imu"].read()

    # Simulate sensor fusion logic
    print("Sensor readings:")
    print(f"  - Camera: {image.shape}")
    print(f"  - Depth: {depth.shape}")
    print(f"  - IMU Acceleration: {acceleration}")
    print(f"  - IMU Gyroscope: {gyroscope}")

    # Your fusion algorithm would go here
    # For example: combine visual and depth data for 3D reconstruction

    assert image is not None
    assert depth is not None
    assert len(acceleration) == 3
    assert len(gyroscope) == 3


def example_test_planning_with_telemetry(mock_pick_and_place):  # noqa: F811
    """Example test for planning system integration."""
    scenario = mock_pick_and_place

    # This is how Sophia's planner might use the scenario

    # 1. Observe the environment
    _ = scenario.get_state()  # Get initial state

    print("Planning pick-and-place operation...")

    # 2. Plan the action sequence (simplified)
    plan = [
        ("move_to_object", "cup"),
        ("grasp_object", "cup"),
        ("move_to_location", "table"),
        ("release_object", None),
    ]

    # 3. Execute the plan
    for action_type, target in plan:
        if action_type == "move_to_object":
            success = scenario.move_to_object(target)
        elif action_type == "grasp_object":
            success = scenario.grasp_object(target)
        elif action_type == "move_to_location":
            success = scenario.move_to_location(target)
        elif action_type == "release_object":
            success = scenario.release_object()

        assert success, f"Action {action_type} failed"
        print(f"  ✓ {action_type}({target})")

    # 4. Verify results
    final_state = scenario.get_state()
    cup_position = final_state["objects"]["cup"]["position"]
    table_position = final_state["locations"]["table"]

    # Cup should be at table location (within tolerance)
    import numpy as np

    distance = np.linalg.norm(np.array(cup_position) - np.array(table_position))
    assert distance < 0.01, "Cup should be at table location"

    print("\nPlan executed successfully!")
    print(f"Telemetry events: {scenario.telemetry.get_event_count()}")


if __name__ == "__main__":
    """
    Note: These examples require pytest to run.
    Run with: pytest examples/fixtures_example.py -v -s
    """
    print("This file contains example tests for Talos fixtures.")
    print("Run with pytest to execute the examples:")
    print("  poetry run pytest examples/fixtures_example.py -v -s")
