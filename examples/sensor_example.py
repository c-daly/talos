"""Example: Using simulated sensors."""

from talos.sensors import SimulatedCamera, SimulatedDepth, SimulatedIMU


def main() -> None:
    """Demonstrate sensor usage."""
    print("Talos Sensors Example\n" + "=" * 50)

    # Create sensors
    camera = SimulatedCamera(resolution=(640, 480))
    depth = SimulatedDepth(resolution=(320, 240))
    imu = SimulatedIMU()

    print("\nCreated sensors:")
    print(f"  Camera: {camera.get_info()}")
    print(f"  Depth: {depth.get_info()}")
    print(f"  IMU: {imu.get_info()}")

    # Read sensor data
    print("\nReading sensor data...")

    image = camera.read()
    print(f"  Camera image shape: {image.shape}, dtype: {image.dtype}")

    depth_map = depth.read()
    print(f"  Depth map shape: {depth_map.shape}, dtype: {depth_map.dtype}")
    print(f"  Depth range: {depth_map.min():.2f}m to {depth_map.max():.2f}m")

    acceleration, gyroscope = imu.read()
    print(f"  Acceleration: {acceleration}")
    print(f"  Gyroscope: {gyroscope}")


if __name__ == "__main__":
    main()
