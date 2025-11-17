"""Simulated camera sensor."""

from typing import Tuple
import numpy as np
from talos.sensors.base import Sensor


class SimulatedCamera(Sensor):
    """Simulated RGB camera sensor.

    Generates synthetic image data for testing purposes.
    """

    def __init__(
        self, name: str = "camera", resolution: Tuple[int, int] = (640, 480)
    ) -> None:
        """Initialize simulated camera.

        Args:
            name: Unique identifier for this camera
            resolution: Image resolution as (width, height)
        """
        super().__init__(name)
        self.resolution = resolution
        self._frame_count = 0

    def read(self) -> np.ndarray:
        """Read current camera frame.

        Returns:
            RGB image as numpy array of shape (height, width, 3) with values 0-255
        """
        if not self._enabled:
            raise RuntimeError(f"Sensor {self.name} is disabled")

        # Generate synthetic image data with varying pattern
        height, width = self.resolution[1], self.resolution[0]
        image = np.zeros((height, width, 3), dtype=np.uint8)

        # Create a simple gradient pattern that changes over time
        offset = self._frame_count % 256
        for i in range(height):
            for j in range(width):
                image[i, j, 0] = (i + offset) % 256  # Red channel
                image[i, j, 1] = (j + offset) % 256  # Green channel
                image[i, j, 2] = ((i + j) + offset) % 256  # Blue channel

        self._frame_count += 1
        return image

    def get_info(self) -> dict:
        """Get camera information.

        Returns:
            Dictionary containing camera metadata
        """
        info = super().get_info()
        info.update(
            {
                "resolution": self.resolution,
                "frame_count": self._frame_count,
            }
        )
        return info
