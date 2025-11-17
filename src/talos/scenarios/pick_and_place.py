"""Pick and place scenario simulation."""

from typing import Dict, Any, List, Tuple
import numpy as np
from talos.sensors import SimulatedCamera, SimulatedDepth, SimulatedIMU
from talos.actuators import SimulatedMotor, SimulatedGripper


class PickAndPlaceScenario:
    """Simulated pick and place scenario.

    This scenario simulates a robotic arm with a gripper that can pick up
    objects and place them at different locations.
    """

    def __init__(self) -> None:
        """Initialize pick and place scenario."""
        # Create sensors
        self.camera = SimulatedCamera(name="arm_camera")
        self.depth = SimulatedDepth(name="arm_depth")
        self.imu = SimulatedIMU(name="arm_imu")

        # Create actuators (simple 3-joint arm + gripper)
        self.joint1 = SimulatedMotor(
            name="joint1", min_position=-1.57, max_position=1.57
        )
        self.joint2 = SimulatedMotor(
            name="joint2", min_position=-1.57, max_position=1.57
        )
        self.joint3 = SimulatedMotor(
            name="joint3", min_position=-1.57, max_position=1.57
        )
        self.gripper = SimulatedGripper(name="gripper")

        # Define objects in the scene
        self.objects = {
            "cup": {"position": np.array([0.3, 0.0, 0.1]), "grasped": False},
            "block": {"position": np.array([0.2, 0.1, 0.1]), "grasped": False},
        }

        # Define locations
        self.locations = {
            "table": np.array([0.4, 0.0, 0.0]),
            "shelf": np.array([0.3, 0.2, 0.3]),
            "home": np.array([0.0, 0.0, 0.2]),
        }

        # Current end effector position (simplified)
        self.end_effector_position = np.array([0.0, 0.0, 0.2])
        self.action_history: List[str] = []

    def get_state(self) -> Dict[str, Any]:
        """Get current scenario state.

        Returns:
            Dictionary containing full scenario state
        """
        return {
            "end_effector_position": self.end_effector_position.tolist(),
            "joint_positions": [
                self.joint1.get_position(),
                self.joint2.get_position(),
                self.joint3.get_position(),
            ],
            "gripper_state": self.gripper.get_state(),
            "objects": {
                name: {
                    "position": obj["position"].tolist(),
                    "grasped": obj["grasped"],
                }
                for name, obj in self.objects.items()
            },
            "locations": {name: pos.tolist() for name, pos in self.locations.items()},
            "action_history": self.action_history,
        }

    def move_to_object(self, object_name: str) -> bool:
        """Move arm to object position.

        Args:
            object_name: Name of the object to move to

        Returns:
            True if successful, False otherwise
        """
        if object_name not in self.objects:
            return False

        target_pos = self.objects[object_name]["position"]
        self.end_effector_position = target_pos.copy()

        # Update joint positions (simplified kinematics)
        self.joint1.set_position(np.arctan2(target_pos[1], target_pos[0]))
        self.joint2.set_position(target_pos[2] / 0.3)
        self.joint3.set_position(0.0)

        self.action_history.append(f"move_to_object({object_name})")
        return True

    def move_to_location(self, location_name: str) -> bool:
        """Move arm to named location.

        Args:
            location_name: Name of the location to move to

        Returns:
            True if successful, False otherwise
        """
        if location_name not in self.locations:
            return False

        target_pos = self.locations[location_name]
        self.end_effector_position = target_pos.copy()

        # Update joint positions (simplified kinematics)
        self.joint1.set_position(np.arctan2(target_pos[1], target_pos[0]))
        self.joint2.set_position(target_pos[2] / 0.3)
        self.joint3.set_position(0.0)

        # If holding an object, move it too
        grasped_obj = self.gripper.get_grasped_object()
        if grasped_obj and grasped_obj in self.objects:
            self.objects[grasped_obj]["position"] = target_pos.copy()

        self.action_history.append(f"move_to_location({location_name})")
        return True

    def grasp_object(self, object_name: str) -> bool:
        """Grasp an object.

        Args:
            object_name: Name of the object to grasp

        Returns:
            True if grasp was successful, False otherwise
        """
        if object_name not in self.objects:
            return False

        obj = self.objects[object_name]

        # Check if end effector is close enough
        distance = np.linalg.norm(self.end_effector_position - obj["position"])
        if distance > 0.05:  # 5cm threshold
            return False

        # Close gripper and grasp
        self.gripper.close()
        success = self.gripper.grasp(object_name)

        if success:
            obj["grasped"] = True
            self.action_history.append(f"grasp_object({object_name})")

        return success

    def release_object(self) -> bool:
        """Release currently grasped object.

        Returns:
            True if release was successful, False otherwise
        """
        grasped_obj = self.gripper.get_grasped_object()
        if not grasped_obj:
            return False

        if grasped_obj in self.objects:
            self.objects[grasped_obj]["grasped"] = False
            self.objects[grasped_obj]["position"] = self.end_effector_position.copy()

        self.gripper.release()
        self.action_history.append("release_object()")
        return True

    def reset(self) -> None:
        """Reset scenario to initial state."""
        # Reset objects
        self.objects["cup"]["position"] = np.array([0.3, 0.0, 0.1])
        self.objects["cup"]["grasped"] = False
        self.objects["block"]["position"] = np.array([0.2, 0.1, 0.1])
        self.objects["block"]["grasped"] = False

        # Reset arm to home position
        self.end_effector_position = np.array([0.0, 0.0, 0.2])
        self.joint1.set_position(0.0)
        self.joint2.set_position(0.0)
        self.joint3.set_position(0.0)
        self.gripper.open()

        # Clear history
        self.action_history = []

    def execute_pick_and_place(
        self, object_name: str, target_location: str
    ) -> Tuple[bool, List[str]]:
        """Execute a complete pick and place sequence.

        Args:
            object_name: Name of object to pick
            target_location: Name of target location

        Returns:
            Tuple of (success, action_log)
        """
        actions = []

        # Move to object
        if not self.move_to_object(object_name):
            return False, actions + ["Failed to move to object"]
        actions.append(f"Moved to {object_name}")

        # Grasp object
        if not self.grasp_object(object_name):
            return False, actions + ["Failed to grasp object"]
        actions.append(f"Grasped {object_name}")

        # Move to target location
        if not self.move_to_location(target_location):
            return False, actions + ["Failed to move to location"]
        actions.append(f"Moved to {target_location}")

        # Release object
        if not self.release_object():
            return False, actions + ["Failed to release object"]
        actions.append("Released object")

        return True, actions
