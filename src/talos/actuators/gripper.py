"""Simulated gripper actuator."""

from typing import Dict, Any, Optional
from talos.actuators.base import Actuator
from talos.telemetry import TelemetryRecorder, EventType


class SimulatedGripper(Actuator):
    """Simulated gripper actuator.

    Simulates a parallel jaw gripper that can open and close.
    """

    def __init__(
        self,
        name: str = "gripper",
        max_opening: float = 0.08,
        telemetry: Optional[TelemetryRecorder] = None,
    ) -> None:
        """Initialize simulated gripper.

        Args:
            name: Unique identifier for this gripper
            max_opening: Maximum opening width in meters
            telemetry: Optional telemetry recorder for tracking events
        """
        super().__init__(name)
        self.max_opening = max_opening
        self._opening = max_opening  # Start fully open
        self._is_grasping = False
        self._grasped_object: Optional[str] = None
        self.telemetry = telemetry or TelemetryRecorder()

    def open(self, opening: Optional[float] = None) -> None:
        """Open the gripper.

        Args:
            opening: Target opening width in meters (default: max_opening)
        """
        if not self._enabled:
            raise RuntimeError(f"Actuator {self.name} is disabled")

        if opening is None:
            opening = self.max_opening

        # Clamp to valid range
        clamped_opening = max(0.0, min(self.max_opening, opening))
        previous_opening = self._opening
        self._opening = clamped_opening

        # If opening beyond threshold, release any grasped object
        released_object = None
        if clamped_opening > 0.01:
            released_object = self._grasped_object
            self._is_grasping = False
            self._grasped_object = None

        # Record telemetry
        self.telemetry.record_event(
            EventType.GRIPPER_OPENED,
            self.name,
            {
                "requested_opening": opening,
                "clamped_opening": clamped_opening,
                "previous_opening": previous_opening,
                "released_object": released_object,
            },
        )

    def close(self, force: float = 1.0) -> None:
        """Close the gripper.

        Args:
            force: Grasping force (normalized 0-1)
        """
        if not self._enabled:
            raise RuntimeError(f"Actuator {self.name} is disabled")

        previous_opening = self._opening
        self._opening = 0.0

        # Simulate grasping if force is sufficient
        if force > 0.5:
            self._is_grasping = True

        # Record telemetry
        self.telemetry.record_event(
            EventType.GRIPPER_CLOSED,
            self.name,
            {
                "force": force,
                "previous_opening": previous_opening,
                "is_grasping": self._is_grasping,
            },
        )

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
        success = False
        if self._opening < 0.01:
            self._is_grasping = True
            self._grasped_object = object_name
            success = True

        # Record telemetry
        self.telemetry.record_event(
            EventType.OBJECT_GRASPED,
            self.name,
            {
                "object_name": object_name,
                "success": success,
                "opening": self._opening,
            },
        )

        return success

    def release(self) -> None:
        """Release any grasped object."""
        if not self._enabled:
            raise RuntimeError(f"Actuator {self.name} is disabled")

        released_object = self._grasped_object

        # Record telemetry before releasing
        self.telemetry.record_event(
            EventType.OBJECT_RELEASED,
            self.name,
            {
                "object_name": released_object,
            },
        )

        self.open()

    def is_grasping(self) -> bool:
        """Check if gripper is currently grasping an object.

        Returns:
            True if grasping, False otherwise
        """
        return self._is_grasping

    def get_grasped_object(self) -> Optional[str]:
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
