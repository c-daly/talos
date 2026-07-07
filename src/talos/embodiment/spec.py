from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class Tier(str, Enum):
    CORE = "core"
    EXT = "ext"


class Clock(str, Enum):
    DRIVEN = "driven"
    REALTIME = "realtime"


@dataclass(frozen=True)
class Space:
    dtype: str
    shape: tuple[int, ...]
    low: Optional[tuple[float, ...]] = None
    high: Optional[tuple[float, ...]] = None
    units: str = ""
    frame: str = "body"

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Space":
        def _t(v: Any) -> Optional[tuple[float, ...]]:
            return tuple(float(x) for x in v) if v is not None else None

        return cls(
            dtype=d["dtype"],
            shape=tuple(d["shape"]),
            low=_t(d.get("low")),
            high=_t(d.get("high")),
            units=d.get("units", ""),
            frame=d.get("frame", "body"),
        )


@dataclass(frozen=True)
class SensorSpec:
    name: str
    space: Space
    rate_hz: float
    tier: Tier = Tier.CORE


@dataclass(frozen=True)
class ActuatorSpec:
    name: str
    space: Space
    tier: Tier = Tier.CORE


@dataclass(frozen=True)
class EntitySpec:
    entity_id: str
    kind: str
    world_frame: str
    clock: Clock
    sensors: tuple[SensorSpec, ...]
    actuators: tuple[ActuatorSpec, ...]

    def actuator(self, name: str) -> ActuatorSpec:
        for a in self.actuators:
            if a.name == name:
                return a
        raise KeyError(name)

    @classmethod
    def from_manifest(cls, d: dict[str, Any]) -> "EntitySpec":
        return cls(
            entity_id=d["entity_id"],
            kind=d["kind"],
            world_frame=d["world_frame"],
            clock=Clock(d["clock"]),
            sensors=tuple(
                SensorSpec(
                    s["name"],
                    Space.from_dict(s),
                    float(s["rate_hz"]),
                    Tier(s.get("tier", "core")),
                )
                for s in d["sensors"]
            ),
            actuators=tuple(
                ActuatorSpec(a["name"], Space.from_dict(a), Tier(a.get("tier", "core")))
                for a in d["actuators"]
            ),
        )


@dataclass(frozen=True)
class StepResult:
    obs: dict[str, Any]
    sim_time: float
    extras: dict[str, Any] = field(default_factory=dict)


def validate_command(spec: EntitySpec, cmd: dict[str, Any]) -> None:
    """Raise ValueError if cmd names an unknown actuator, wrong shape, or out of bounds."""
    for name, value in cmd.items():
        try:
            act = spec.actuator(name)
        except KeyError:
            raise ValueError(f"unknown actuator: {name}")
        (n,) = act.space.shape
        if len(value) != n:
            raise ValueError(f"{name}: shape expected {n}, got {len(value)}")
        lo, hi = act.space.low, act.space.high
        for i, v in enumerate(value):
            if lo is not None and v < lo[i]:
                raise ValueError(f"{name}[{i}]={v} below bounds {lo[i]}")
            if hi is not None and v > hi[i]:
                raise ValueError(f"{name}[{i}]={v} above bounds {hi[i]}")
