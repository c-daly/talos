import pytest
from talos.embodiment.spec import EntitySpec, Clock, Tier, validate_command

MANIFEST = {
    "type": "manifest",
    "entity_id": "creature-0",
    "kind": "sim",
    "world_frame": "3d",
    "clock": "realtime",
    "sensors": [
        {
            "name": "odom",
            "dtype": "float32",
            "shape": [6],
            "units": "m,m/s,rad,rad/s",
            "frame": "world",
            "rate_hz": 20,
            "tier": "core",
        }
    ],
    "actuators": [
        {
            "name": "cmd_vel",
            "dtype": "float32",
            "shape": [2],
            "low": [0.0, -1.5],
            "high": [2.0, 1.5],
            "units": "m/s,rad/s",
            "frame": "body",
            "tier": "core",
        }
    ],
}


def test_from_manifest_parses_specs():
    spec = EntitySpec.from_manifest(MANIFEST)
    assert spec.entity_id == "creature-0"
    assert spec.clock is Clock.REALTIME
    assert spec.sensors[0].name == "odom"
    assert spec.sensors[0].space.shape == (6,)
    act = spec.actuator("cmd_vel")
    assert act.tier is Tier.CORE
    assert act.space.low == (0.0, -1.5)


def test_validate_command_accepts_in_bounds():
    spec = EntitySpec.from_manifest(MANIFEST)
    validate_command(spec, {"cmd_vel": [1.0, 0.5]})  # no raise


@pytest.mark.parametrize(
    "cmd, msg",
    [
        ({"steer": [1.0, 0.0]}, "unknown actuator"),
        ({"cmd_vel": [1.0]}, "shape"),
        ({"cmd_vel": [5.0, 0.0]}, "bounds"),
        ({"cmd_vel": [1.0, -9.0]}, "bounds"),
    ],
)
def test_validate_command_rejects(cmd, msg):
    spec = EntitySpec.from_manifest(MANIFEST)
    with pytest.raises(ValueError, match=msg):
        validate_command(spec, cmd)
