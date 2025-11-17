"""Base class for all actuators."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class Actuator(ABC):
    """Abstract base class for all actuators.

    All actuators must implement control methods specific to their type.
    """

    def __init__(self, name: str) -> None:
        """Initialize actuator.

        Args:
            name: Unique identifier for this actuator
        """
        self.name = name
        self._enabled = True

    def enable(self) -> None:
        """Enable the actuator."""
        self._enabled = True

    def disable(self) -> None:
        """Disable the actuator."""
        self._enabled = False

    def is_enabled(self) -> bool:
        """Check if actuator is enabled.

        Returns:
            True if actuator is enabled, False otherwise
        """
        return self._enabled

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Get current actuator state.

        Returns:
            Dictionary containing actuator state
        """
        pass

    def get_info(self) -> Dict[str, Any]:
        """Get actuator information.

        Returns:
            Dictionary containing actuator metadata
        """
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "enabled": self._enabled,
        }
