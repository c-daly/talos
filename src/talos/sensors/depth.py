"""Simulated depth sensor."""

from typing import Tuple
import numpy as np
import numpy.typing as npt
from talos.sensors.base import Sensor


class SimulatedDepth(Sensor):
    """Simulated depth sensor.

    Generates synthetic depth map data for testing purposes.
    """

    def __init__(
        self,
        name: str = "depth",
        resolution: Tuple[int, int] = (320, 240),
        min_range: float = 0.5,
        max_range: float = 5.0,
    ) -> None:
        """Initialize simulated depth sensor.

        Args:
            name: Unique identifier for this sensor
            resolution: Depth map resolution as (width, height)
            min_range: Minimum depth range in meters
            max_range: Maximum depth range in meters
        """
        super().__init__(name)
        self.resolution = resolution
        self.min_range = min_range
        self.max_range = max_range
        self._frame_count = 0

    def read(self) -> npt.NDArray[np.float32]:
        """Read current depth map.

        Returns:
            Depth map as numpy array of shape (height, width) with values in meters
        """
        if not self._enabled:
            raise RuntimeError(f"Sensor {self.name} is disabled")

        # Generate synthetic depth data
        height, width = self.resolution[1], self.resolution[0]

        # Create a depth gradient that simulates objects at different distances
        # Objects closer to center appear closer
        center_y, center_x = height // 2, width // 2
        y_coords, x_coords = np.ogrid[:height, :width]

        # Calculate distance from center
        dist_from_center = np.sqrt(
            ((x_coords - center_x) / width) ** 2 + ((y_coords - center_y) / height) ** 2
        )

        # Map to depth range (closer at center, farther at edges)
        depth_map = (
            self.min_range + (self.max_range - self.min_range) * dist_from_center
        )

        # Add some noise to make it more realistic
        noise = np.random.normal(0, 0.01, depth_map.shape)
        depth_map = depth_map + noise

        # Add slight variation over time
        time_offset = np.sin(self._frame_count * 0.1) * 0.05
        depth_map = depth_map + time_offset

        self._frame_count += 1
        result: npt.NDArray[np.float32] = depth_map.astype(np.float32)
        return result

    def get_info(self) -> dict:
        """Get depth sensor information.

        Returns:
            Dictionary containing sensor metadata
        """
        info = super().get_info()
        info.update(
            {
                "resolution": self.resolution,
                "min_range": self.min_range,
                "max_range": self.max_range,
                "frame_count": self._frame_count,
            }
        )
        return info
