"""Simulated gripper actuator."""

from typing import Dict, Any
from talos.actuators.base import Actuator


class SimulatedGripper(Actuator):
    """Simulated gripper actuator.

    Simulates a parallel jaw gripper that can open and close.
    """

    def __init__(self, name: str = "gripper", max_opening: float = 0.08) -> None:
        """Initialize simulated gripper.

        Args:
            name: Unique identifier for this gripper
            max_opening: Maximum opening width in meters
        """
        super().__init__(name)
        self.max_opening = max_opening
        self._opening = max_opening  # Start fully open
        self._is_grasping = False
        self._grasped_object = None

    def open(self, opening: float = None) -> None:
        """Open the gripper.

        Args:
            opening: Target opening width in meters (default: max_opening)
        """
        if not self._enabled:
            raise RuntimeError(f"Actuator {self.name} is disabled")

        if opening is None:
            opening = self.max_opening

        # Clamp to valid range
        opening = max(0.0, min(self.max_opening, opening))
        self._opening = opening

        # If opening beyond threshold, release any grasped object
        if opening > 0.01:
            self._is_grasping = False
            self._grasped_object = None

    def close(self, force: float = 1.0) -> None:
        """Close the gripper.

        Args:
            force: Grasping force (normalized 0-1)
        """
        if not self._enabled:
            raise RuntimeError(f"Actuator {self.name} is disabled")

        self._opening = 0.0
        # Simulate grasping if force is sufficient
        if force > 0.5:
            self._is_grasping = True

    def grasp(self, object_name: str) -> bool:
        """Attempt to grasp an object.

        Args:
            object_name: Name of the object to grasp

        Returns:
            True if grasp was successful, False otherwise
        """
        if not self._enabled:
            raise RuntimeError(f"Actuator {self.name} is disabled")

        # Simulate successful grasp if gripper is closed
        if self._opening < 0.01:
            self._is_grasping = True
            self._grasped_object = object_name
            return True

        return False

    def release(self) -> None:
        """Release any grasped object."""
        if not self._enabled:
            raise RuntimeError(f"Actuator {self.name} is disabled")

        self.open()

    def is_grasping(self) -> bool:
        """Check if gripper is currently grasping an object.

        Returns:
            True if grasping, False otherwise
        """
        return self._is_grasping

    def get_grasped_object(self) -> str:
        """Get the name of the currently grasped object.

        Returns:
            Object name or None if not grasping
        """
        return self._grasped_object

    def get_state(self) -> Dict[str, Any]:
        """Get current gripper state.

        Returns:
            Dictionary containing gripper state
        """
        return {
            "opening": self._opening,
            "is_grasping": self._is_grasping,
            "grasped_object": self._grasped_object,
        }

    def get_info(self) -> Dict[str, Any]:
        """Get gripper information.

        Returns:
            Dictionary containing gripper metadata
        """
        info = super().get_info()
        info.update(
            {
                "max_opening": self.max_opening,
            }
        )
        return info
