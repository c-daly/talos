"""Simulated IMU (Inertial Measurement Unit) sensor."""

from typing import Tuple
import numpy as np
from talos.sensors.base import Sensor


class SimulatedIMU(Sensor):
    """Simulated Inertial Measurement Unit (IMU) sensor.

    Provides simulated accelerometer and gyroscope data.
    """

    def __init__(self, name: str = "imu") -> None:
        """Initialize simulated IMU.

        Args:
            name: Unique identifier for this IMU
        """
        super().__init__(name)
        self._sample_count = 0
        # Simulate gravity
        self._gravity = np.array([0.0, 0.0, -9.81])

    def read(self) -> Tuple[np.ndarray, np.ndarray]:
        """Read current IMU data.

        Returns:
            Tuple of (acceleration, gyroscope) where:
            - acceleration: 3D vector in m/s^2 (x, y, z)
            - gyroscope: 3D angular velocity vector in rad/s (x, y, z)
        """
        if not self._enabled:
            raise RuntimeError(f"Sensor {self.name} is disabled")

        # Simulate accelerometer data (gravity + noise)
        accel_noise = np.random.normal(0, 0.1, 3)
        acceleration = self._gravity + accel_noise

        # Simulate gyroscope data (small random motion)
        gyro_noise = np.random.normal(0, 0.05, 3)
        # Add a small sinusoidal component to simulate movement
        time = self._sample_count * 0.01  # Assuming 100Hz sample rate
        gyroscope = (
            np.array(
                [
                    0.1 * np.sin(time),
                    0.1 * np.cos(time),
                    0.05 * np.sin(2 * time),
                ]
            )
            + gyro_noise
        )

        self._sample_count += 1
        return acceleration.astype(np.float32), gyroscope.astype(np.float32)

    def get_info(self) -> dict:
        """Get IMU information.

        Returns:
            Dictionary containing IMU metadata
        """
        info = super().get_info()
        info.update(
            {
                "sample_count": self._sample_count,
                "gravity": self._gravity.tolist(),
            }
        )
        return info
