"""Base class for all sensors."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class Sensor(ABC):
    """Abstract base class for all sensors.

    All sensors must implement the read() method to return sensor data.
    """

    def __init__(self, name: str) -> None:
        """Initialize sensor.

        Args:
            name: Unique identifier for this sensor
        """
        self.name = name
        self._enabled = True

    @abstractmethod
    def read(self) -> Any:
        """Read current sensor data.

        Returns:
            Sensor-specific data format
        """
        pass

    def enable(self) -> None:
        """Enable the sensor."""
        self._enabled = True

    def disable(self) -> None:
        """Disable the sensor."""
        self._enabled = False

    def is_enabled(self) -> bool:
        """Check if sensor is enabled.

        Returns:
            True if sensor is enabled, False otherwise
        """
        return self._enabled

    def get_info(self) -> Dict[str, Any]:
        """Get sensor information.

        Returns:
            Dictionary containing sensor metadata
        """
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "enabled": self._enabled,
        }
