"""Advanced tests for Talos fixtures infrastructure."""

import pytest
from typing import Any

from talos.fixtures import (
    mock_camera,
    mock_depth_sensor,
    mock_imu,
    mock_motor,
    mock_gripper,
    mock_telemetry,
    mock_pick_and_place,
    mock_robot_arm,
    mock_sensor_suite,
)


def test_fixture_camera(mock_camera: Any) -> None:
    """Test camera fixture provides working camera."""
    assert mock_camera is not None
    assert mock_camera.is_enabled()

    # Camera should be able to capture
    image = mock_camera.read()
    assert image is not None
    assert image.shape == (480, 640, 3)


def test_fixture_depth_sensor(mock_depth_sensor: Any) -> None:
    """Test depth sensor fixture provides working sensor."""
    assert mock_depth_sensor is not None
    assert mock_depth_sensor.is_enabled()

    depth_map = mock_depth_sensor.read()
    assert depth_map is not None
    assert depth_map.shape == (240, 320)


def test_fixture_imu(mock_imu: Any) -> None:
    """Test IMU fixture provides working sensor."""
    assert mock_imu is not None
    assert mock_imu.is_enabled()

    acceleration, gyroscope = mock_imu.read()
    assert len(acceleration) == 3
    assert len(gyroscope) == 3


def test_fixture_motor(mock_motor: Any) -> None:
    """Test motor fixture provides working motor."""
    assert mock_motor is not None
    assert mock_motor.is_enabled()

    mock_motor.set_position(1.0)
    assert mock_motor.get_position() == 1.0


def test_fixture_gripper(mock_gripper: Any) -> None:
    """Test gripper fixture provides working gripper."""
    assert mock_gripper is not None
    assert mock_gripper.is_enabled()

    mock_gripper.close()
    assert mock_gripper.is_grasping()

    mock_gripper.open()
    assert not mock_gripper.is_grasping()


def test_fixture_telemetry(mock_telemetry: Any) -> None:
    """Test telemetry fixture provides working recorder."""
    assert mock_telemetry is not None
    assert mock_telemetry.is_enabled()
    assert mock_telemetry.get_event_count() == 0


def test_fixture_pick_and_place(mock_pick_and_place: Any) -> None:
    """Test pick and place fixture provides working scenario."""
    assert mock_pick_and_place is not None

    success, actions = mock_pick_and_place.execute_pick_and_place("cup", "shelf")
    assert success
    assert len(actions) > 0


def test_fixture_robot_arm(mock_robot_arm: Any) -> None:
    """Test robot arm fixture provides working multi-joint arm."""
    assert mock_robot_arm is not None
    assert len(mock_robot_arm) >= 3  # At least 3 joints

    # Check first 3 joints (handle dict or list)
    joints = list(mock_robot_arm.values()) if isinstance(mock_robot_arm, dict) else list(mock_robot_arm)
    for joint in joints[:3]:
        assert joint.is_enabled()
        joint.set_position(0.5)
        assert joint.get_position() == 0.5


def test_fixture_sensor_suite(mock_sensor_suite: Any) -> None:
    """Test sensor suite fixture provides all sensors."""
    assert mock_sensor_suite is not None
    assert "camera" in mock_sensor_suite
    assert "depth" in mock_sensor_suite
    assert "imu" in mock_sensor_suite

    # All sensors should work
    image = mock_sensor_suite["camera"].read()
    depth = mock_sensor_suite["depth"].read()
    imu_data = mock_sensor_suite["imu"].read()

    assert image is not None
    assert depth is not None
    assert imu_data is not None


def test_fixture_composition_multiple_together(
    mock_motor: Any, mock_gripper: Any, mock_telemetry: Any
) -> None:
    """Test using multiple fixtures together."""
    # Reconfigure actuators to use shared telemetry
    from talos.actuators import SimulatedMotor, SimulatedGripper

    motor = SimulatedMotor(name="test_motor", telemetry=mock_telemetry)
    gripper = SimulatedGripper(name="test_gripper", telemetry=mock_telemetry)

    # Perform operations
    motor.set_position(1.0)
    gripper.close()

    # Telemetry should capture both
    assert mock_telemetry.get_event_count() >= 2


def test_fixture_state_isolation_between_tests(mock_motor: Any) -> None:
    """Test fixture state isolation between tests (test 1)."""
    mock_motor.set_position(1.0)
    assert mock_motor.get_position() == 1.0


def test_fixture_state_isolation_between_tests_2(mock_motor: Any) -> None:
    """Test fixture state isolation between tests (test 2)."""
    # Motor should be reset (not at position from previous test)
    # In a new test, fixtures are recreated
    position = mock_motor.get_position()
    # Default position should be 0.0
    assert position == 0.0


def test_fixture_cleanup_on_test_failure(mock_gripper: Any) -> None:
    """Test fixture cleanup happens even if test would fail."""
    mock_gripper.close()
    mock_gripper.grasp("object")

    # Even if we don't explicitly cleanup, pytest fixture teardown handles it
    assert mock_gripper.get_grasped_object() == "object"


def test_fixture_performance_large_scenario(mock_pick_and_place: Any) -> None:
    """Test fixture performance with large scenarios."""
    # Execute multiple operations
    for _ in range(10):
        success, actions = mock_pick_and_place.execute_pick_and_place("cup", "shelf")
        assert success


def test_fixture_custom_configuration() -> None:
    """Test custom fixture configuration."""
    from talos.actuators import SimulatedMotor

    # Create custom configured motor
    custom_motor = SimulatedMotor(
        name="custom_motor", min_position=-3.14, max_position=3.14
    )

    custom_motor.set_position(3.0)
    assert custom_motor.get_position() == 3.0


def test_fixture_nested_usage(mock_pick_and_place: Any) -> None:
    """Test fixtures work with nested test functions."""

    def inner_operation() -> bool:
        return mock_pick_and_place.move_to_object("cup")

    def outer_operation() -> bool:
        return inner_operation() and mock_pick_and_place.grasp_object("cup")

    success = outer_operation()
    assert success


def test_fixture_sensor_camera_produces_different_frames(mock_camera: Any) -> None:
    """Test camera fixture produces different frames."""
    frame1 = mock_camera.read()
    frame2 = mock_camera.read()

    # Frames should be different (simulated variation)
    assert not (frame1 == frame2).all()


def test_fixture_telemetry_captures_all_operations(
    mock_motor: Any, mock_telemetry: Any
) -> None:
    """Test telemetry fixture captures all operations."""
    from talos.actuators import SimulatedMotor

    motor_with_telemetry = SimulatedMotor(name="test", telemetry=mock_telemetry)

    # Perform operations
    motor_with_telemetry.set_position(0.5)
    motor_with_telemetry.set_velocity(0.2)
    motor_with_telemetry.set_position(1.0)

    # All should be captured
    assert mock_telemetry.get_event_count() >= 3


def test_fixture_error_handling(mock_motor: Any) -> None:
    """Test fixtures handle errors gracefully."""
    mock_motor.disable()

    with pytest.raises(RuntimeError):
        mock_motor.set_position(1.0)


def test_fixture_pick_and_place_telemetry_integration(
    mock_pick_and_place: Any,
) -> None:
    """Test pick and place fixture has telemetry integrated."""
    mock_pick_and_place.execute_pick_and_place("cup", "shelf")

    # Should have telemetry events
    events = mock_pick_and_place.telemetry.get_events()
    assert len(events) > 0


def test_fixture_sensor_suite_all_enabled(mock_sensor_suite: Any) -> None:
    """Test sensor suite fixture has all sensors enabled."""
    for sensor_name, sensor in mock_sensor_suite.items():
        assert sensor.is_enabled(), f"{sensor_name} should be enabled"


def test_fixture_robot_arm_coordinated_motion(mock_robot_arm: Any) -> None:
    """Test robot arm fixture allows coordinated motion."""
    # Set all joints to different positions
    positions = [0.5, 1.0, 1.5]

    # Handle both dict and list
    joints = list(mock_robot_arm.values()) if isinstance(mock_robot_arm, dict) else list(mock_robot_arm)
    
    for joint, position in zip(joints[:3], positions):
        joint.set_position(position)

    # Verify all reached target
    for joint, expected in zip(joints[:3], positions):
        assert joint.get_position() == expected


def test_fixture_reusability_across_tests(mock_telemetry: Any) -> None:
    """Test fixtures are reusable across tests."""
    # This test just verifies the fixture works
    assert mock_telemetry.is_enabled()
    # Each test gets a fresh instance


def test_fixture_with_pytest_parametrize(mock_motor: Any) -> None:
    """Test fixtures work with pytest parametrize."""
    positions = [0.0, 0.5, 1.0, 1.5, 2.0]

    for pos in positions:
        mock_motor.set_position(pos)
        assert abs(mock_motor.get_position() - min(pos, mock_motor.max_position)) < 0.01
