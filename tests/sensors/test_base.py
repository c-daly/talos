"""Tests for sensor base class."""

from talos.sensors.base import Sensor


class ConcreteSensor(Sensor):
    """Concrete sensor implementation for testing."""

    def read(self):
        return "test_data"


def test_sensor_initialization() -> None:
    """Test sensor initialization."""
    sensor = ConcreteSensor(name="test_sensor")
    assert sensor.name == "test_sensor"
    assert sensor.is_enabled()


def test_sensor_enable_disable() -> None:
    """Test sensor enable/disable functionality."""
    sensor = ConcreteSensor(name="test_sensor")

    # Initially enabled
    assert sensor.is_enabled()

    # Disable
    sensor.disable()
    assert not sensor.is_enabled()

    # Re-enable
    sensor.enable()
    assert sensor.is_enabled()


def test_sensor_get_info() -> None:
    """Test sensor info retrieval."""
    sensor = ConcreteSensor(name="test_sensor")
    info = sensor.get_info()

    assert info["name"] == "test_sensor"
    assert info["type"] == "ConcreteSensor"
    assert info["enabled"] is True
