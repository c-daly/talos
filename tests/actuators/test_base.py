"""Tests for actuator base class."""

from talos.actuators.base import Actuator


class ConcreteActuator(Actuator):
    """Concrete actuator implementation for testing."""

    def get_state(self) -> dict[str, str]:
        return {"test": "state"}


def test_actuator_initialization() -> None:
    """Test actuator initialization."""
    actuator = ConcreteActuator(name="test_actuator")
    assert actuator.name == "test_actuator"
    assert actuator.is_enabled()


def test_actuator_enable_disable() -> None:
    """Test actuator enable/disable functionality."""
    actuator = ConcreteActuator(name="test_actuator")

    # Initially enabled
    assert actuator.is_enabled()

    # Disable
    actuator.disable()
    assert not actuator.is_enabled()

    # Re-enable
    actuator.enable()
    assert actuator.is_enabled()


def test_actuator_get_info() -> None:
    """Test actuator info retrieval."""
    actuator = ConcreteActuator(name="test_actuator")
    info = actuator.get_info()

    assert info["name"] == "test_actuator"
    assert info["type"] == "ConcreteActuator"
    assert info["enabled"] is True


def test_actuator_get_state() -> None:
    """Test actuator state retrieval."""
    actuator = ConcreteActuator(name="test_actuator")
    state = actuator.get_state()

    assert state == {"test": "state"}
