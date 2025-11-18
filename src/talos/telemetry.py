"""Telemetry system for tracking actuator and sensor events."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum


class EventType(Enum):
    """Types of telemetry events."""

    POSITION_SET = "position_set"
    VELOCITY_SET = "velocity_set"
    GRIPPER_OPENED = "gripper_opened"
    GRIPPER_CLOSED = "gripper_closed"
    OBJECT_GRASPED = "object_grasped"
    OBJECT_RELEASED = "object_released"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class TelemetryEvent:
    """A single telemetry event."""

    timestamp: datetime
    event_type: EventType
    actuator_name: str
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary.

        Returns:
            Dictionary representation of the event
        """
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "actuator_name": self.actuator_name,
            "data": self.data,
        }


class TelemetryRecorder:
    """Records and manages telemetry events for actuators."""

    def __init__(self, max_events: int = 1000) -> None:
        """Initialize telemetry recorder.

        Args:
            max_events: Maximum number of events to store (oldest are removed)
        """
        self.max_events = max_events
        self._events: List[TelemetryEvent] = []
        self._enabled = True

    def record_event(
        self,
        event_type: EventType,
        actuator_name: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a telemetry event.

        Args:
            event_type: Type of event
            actuator_name: Name of the actuator
            data: Additional event data
        """
        if not self._enabled:
            return

        event = TelemetryEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            actuator_name=actuator_name,
            data=data or {},
        )

        self._events.append(event)

        # Maintain max size by removing oldest events
        if len(self._events) > self.max_events:
            self._events = self._events[-self.max_events :]

    def get_events(
        self,
        actuator_name: Optional[str] = None,
        event_type: Optional[EventType] = None,
        limit: Optional[int] = None,
    ) -> List[TelemetryEvent]:
        """Get recorded telemetry events.

        Args:
            actuator_name: Filter by actuator name
            event_type: Filter by event type
            limit: Maximum number of events to return (most recent)

        Returns:
            List of telemetry events
        """
        events = self._events

        if actuator_name:
            events = [e for e in events if e.actuator_name == actuator_name]

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if limit:
            events = events[-limit:]

        return events

    def get_event_count(
        self,
        actuator_name: Optional[str] = None,
        event_type: Optional[EventType] = None,
    ) -> int:
        """Get count of recorded events.

        Args:
            actuator_name: Filter by actuator name
            event_type: Filter by event type

        Returns:
            Number of events matching the criteria
        """
        return len(self.get_events(actuator_name=actuator_name, event_type=event_type))

    def clear(self) -> None:
        """Clear all recorded events."""
        self._events = []

    def enable(self) -> None:
        """Enable telemetry recording."""
        self._enabled = True

    def disable(self) -> None:
        """Disable telemetry recording."""
        self._enabled = False

    def is_enabled(self) -> bool:
        """Check if telemetry recording is enabled.

        Returns:
            True if enabled, False otherwise
        """
        return self._enabled

    def to_dict(self) -> List[Dict[str, Any]]:
        """Export all events as dictionaries.

        Returns:
            List of event dictionaries
        """
        return [event.to_dict() for event in self._events]
