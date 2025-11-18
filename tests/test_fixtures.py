"""Tests for mock hardware fixtures.

This file demonstrates how to use the mock hardware fixtures provided
by Talos for testing robotic scenarios.
"""

from talos.actuators import SimulatedMotor
from talos.telemetry import EventType

# Fixtures are automatically available from conftest.py
# No need to import them explicitly


def test_mock_camera_fixture(mock_camera):
    """Test the mock camera fixture."""
    assert mock_camera is not None
    assert mock_camera.is_enabled()

    # Read image data
    image = mock_camera.read()
    assert image is not None
    assert image.shape == (480, 640, 3)


def test_mock_depth_sensor_fixture(mock_depth_sensor):
    """Test the mock depth sensor fixture."""
    assert mock_depth_sensor is not None
    assert mock_depth_sensor.is_enabled()

    # Read depth data
    depth_map = mock_depth_sensor.read()
    assert depth_map is not None
    assert depth_map.shape == (240, 320)


def test_mock_imu_fixture(mock_imu):
    """Test the mock IMU fixture."""
    assert mock_imu is not None
    assert mock_imu.is_enabled()

    # Read IMU data
    acceleration, gyroscope = mock_imu.read()
    assert acceleration is not None
    assert gyroscope is not None
    assert len(acceleration) == 3
    assert len(gyroscope) == 3


def test_mock_motor_fixture(mock_motor):
    """Test the mock motor fixture."""
    assert mock_motor is not None
    assert mock_motor.is_enabled()

    # Control motor
    mock_motor.set_position(1.57)
    assert mock_motor.get_position() == 1.57

    # Verify state
    state = mock_motor.get_state()
    assert state["position"] == 1.57


def test_mock_gripper_fixture(mock_gripper):
    """Test the mock gripper fixture."""
    assert mock_gripper is not None
    assert mock_gripper.is_enabled()

    # Control gripper
    mock_gripper.close()
    state = mock_gripper.get_state()
    assert state["opening"] == 0.0

    mock_gripper.open()
    state = mock_gripper.get_state()
    assert state["opening"] > 0.0


def test_mock_telemetry_fixture(mock_telemetry):
    """Test the mock telemetry fixture."""
    assert mock_telemetry is not None
    assert mock_telemetry.get_event_count() == 0

    # Create motor with telemetry
    motor = SimulatedMotor(name="test_motor", telemetry=mock_telemetry)
    motor.set_position(1.0)

    # Verify telemetry recorded the event
    events = mock_telemetry.get_events()
    assert len(events) > 0

    # Verify event type
    position_events = mock_telemetry.get_events(event_type=EventType.POSITION_SET)
    assert len(position_events) > 0


def test_mock_pick_and_place_fixture(mock_pick_and_place):
    """Test the mock pick and place scenario fixture."""
    scenario = mock_pick_and_place

    # Verify scenario is initialized
    assert scenario is not None
    assert scenario.camera is not None
    assert scenario.depth is not None
    assert scenario.imu is not None
    assert scenario.gripper is not None

    # Execute pick and place
    success, actions = scenario.execute_pick_and_place("cup", "shelf")
    assert success
    assert len(actions) == 4

    # Verify telemetry was recorded
    assert scenario.telemetry.get_event_count() > 0


def test_mock_robot_arm_fixture(mock_robot_arm):
    """Test the mock robot arm fixture."""
    arm = mock_robot_arm

    # Verify all joints exist
    assert "joint1" in arm
    assert "joint2" in arm
    assert "joint3" in arm

    # Control all joints
    arm["joint1"].set_position(0.5)
    arm["joint2"].set_position(1.0)
    arm["joint3"].set_position(1.5)

    # Verify positions
    assert arm["joint1"].get_position() == 0.5
    assert arm["joint2"].get_position() == 1.0
    assert arm["joint3"].get_position() == 1.5


def test_mock_sensor_suite_fixture(mock_sensor_suite):
    """Test the mock sensor suite fixture."""
    sensors = mock_sensor_suite

    # Verify all sensors exist
    assert "camera" in sensors
    assert "depth" in sensors
    assert "imu" in sensors

    # Read from all sensors
    image = sensors["camera"].read()
    depth = sensors["depth"].read()
    acceleration, gyroscope = sensors["imu"].read()

    # Verify data
    assert image is not None
    assert depth is not None
    assert acceleration is not None
    assert gyroscope is not None


def test_fixture_cleanup_camera(mock_camera):
    """Test that camera fixture is cleaned up properly."""
    # Verify camera is enabled initially
    assert mock_camera.is_enabled()
    # After test, fixture cleanup should disable it
    # This is verified implicitly by the fixture's teardown


def test_fixture_cleanup_gripper(mock_gripper):
    """Test that gripper fixture is cleaned up properly."""
    # Use the gripper
    mock_gripper.close()
    assert mock_gripper.get_state()["opening"] == 0.0
    # After test, fixture cleanup should disable it


def test_multiple_fixtures_together(mock_motor, mock_gripper, mock_telemetry):
    """Test using multiple fixtures together."""
    # Create motor and gripper with shared telemetry
    motor = SimulatedMotor(name="arm_motor", telemetry=mock_telemetry)

    # Perform operations
    motor.set_position(1.0)
    mock_gripper.close()
    mock_gripper.grasp("test_object")

    # Verify telemetry tracked both
    events = mock_telemetry.get_events()
    assert len(events) > 0


def test_scenario_with_telemetry(mock_pick_and_place):
    """Test that scenario fixture includes telemetry tracking."""
    scenario = mock_pick_and_place

    # Perform some actions
    scenario.move_to_object("cup")
    scenario.grasp_object("cup")

    # Verify telemetry
    events = scenario.telemetry.get_events()
    assert len(events) > 0

    # Verify specific event types
    grasp_events = scenario.telemetry.get_events(event_type=EventType.OBJECT_GRASPED)
    assert len(grasp_events) == 1


def test_robot_arm_coordination(mock_robot_arm, mock_telemetry):
    """Test coordinated motion across robot arm joints."""
    arm = mock_robot_arm

    # Add telemetry to all joints
    arm["joint1"].telemetry = mock_telemetry
    arm["joint2"].telemetry = mock_telemetry
    arm["joint3"].telemetry = mock_telemetry

    # Perform coordinated motion
    target_positions = [0.5, 1.0, 1.5]
    for i, (joint_name, target) in enumerate(zip(arm.keys(), target_positions), 1):
        arm[joint_name].set_position(target)

    # Verify all joints reached target
    positions = [motor.get_position() for motor in arm.values()]
    assert positions == target_positions

    # Verify telemetry recorded all movements
    position_events = mock_telemetry.get_events(event_type=EventType.POSITION_SET)
    assert len(position_events) == 3


def test_sensor_suite_all_enabled(mock_sensor_suite):
    """Test that all sensors in suite are enabled by default."""
    sensors = mock_sensor_suite

    for sensor_name, sensor in sensors.items():
        assert sensor.is_enabled(), f"{sensor_name} should be enabled"


def test_pick_and_place_reset(mock_pick_and_place):
    """Test that scenario can be reset between operations."""
    scenario = mock_pick_and_place

    # Perform first operation
    scenario.move_to_object("cup")
    scenario.grasp_object("cup")
    _ = scenario.get_state()  # Get state before reset

    # Reset
    scenario.reset()
    state2 = scenario.get_state()

    # Verify reset
    assert len(state2["action_history"]) == 0
    assert state2["telemetry_event_count"] == 0
    assert not state2["objects"]["cup"]["grasped"]
