"""Simulated motor actuator."""

from typing import Dict, Any, Optional
from talos.actuators.base import Actuator
from talos.telemetry import TelemetryRecorder, EventType


class SimulatedMotor(Actuator):
    """Simulated motor actuator.

    Simulates a rotary motor with position and velocity control.
    """

    def __init__(
        self,
        name: str = "motor",
        min_position: float = -3.14,
        max_position: float = 3.14,
        max_velocity: float = 1.0,
        telemetry: Optional[TelemetryRecorder] = None,
    ) -> None:
        """Initialize simulated motor.

        Args:
            name: Unique identifier for this motor
            min_position: Minimum position in radians
            max_position: Maximum position in radians
            max_velocity: Maximum velocity in rad/s
            telemetry: Optional telemetry recorder for tracking events
        """
        super().__init__(name)
        self.min_position = min_position
        self.max_position = max_position
        self.max_velocity = max_velocity
        self._position = 0.0
        self._velocity = 0.0
        self._target_position = 0.0
        self.telemetry = telemetry or TelemetryRecorder()

    def set_position(self, position: float) -> None:
        """Set target position for the motor.

        Args:
            position: Target position in radians
        """
        if not self._enabled:
            raise RuntimeError(f"Actuator {self.name} is disabled")

        # Clamp to valid range
        clamped_position = max(self.min_position, min(self.max_position, position))
        self._target_position = clamped_position

        # Record telemetry
        self.telemetry.record_event(
            EventType.POSITION_SET,
            self.name,
            {
                "requested_position": position,
                "clamped_position": clamped_position,
                "previous_position": self._position,
            },
        )

        # Simulate instant movement for now (Phase 1 simplification)
        self._position = clamped_position
        self._velocity = 0.0

    def set_velocity(self, velocity: float) -> None:
        """Set motor velocity.

        Args:
            velocity: Target velocity in rad/s
        """
        if not self._enabled:
            raise RuntimeError(f"Actuator {self.name} is disabled")

        # Clamp to valid range
        clamped_velocity = max(-self.max_velocity, min(self.max_velocity, velocity))

        # Record telemetry
        self.telemetry.record_event(
            EventType.VELOCITY_SET,
            self.name,
            {
                "requested_velocity": velocity,
                "clamped_velocity": clamped_velocity,
                "previous_velocity": self._velocity,
            },
        )

        self._velocity = clamped_velocity

    def get_position(self) -> float:
        """Get current motor position.

        Returns:
            Current position in radians
        """
        return self._position

    def get_velocity(self) -> float:
        """Get current motor velocity.

        Returns:
            Current velocity in rad/s
        """
        return self._velocity

    def get_state(self) -> Dict[str, Any]:
        """Get current motor state.

        Returns:
            Dictionary containing motor state
        """
        return {
            "position": self._position,
            "velocity": self._velocity,
            "target_position": self._target_position,
        }

    def get_info(self) -> Dict[str, Any]:
        """Get motor information.

        Returns:
            Dictionary containing motor metadata
        """
        info = super().get_info()
        info.update(
            {
                "min_position": self.min_position,
                "max_position": self.max_position,
                "max_velocity": self.max_velocity,
            }
        )
        return info
