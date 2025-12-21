# Talos

[![CI](https://github.com/c-daly/talos/actions/workflows/ci.yml/badge.svg)](https://github.com/c-daly/talos/actions/workflows/ci.yml)

**Sensor/actuator abstraction layer for [Project LOGOS](https://github.com/c-daly/logos)**

Talos provides hardware abstraction: simulated sensors (camera, depth, IMU) and actuators (motors, grippers) for developing the cognitive architecture without physical hardware.

## Quick Start

```bash
# Install
poetry install

# Test
poetry run pytest tests/unit/ -v

# Run examples
poetry run python examples/sensor_example.py
```

### Docker

```bash
docker pull ghcr.io/c-daly/talos:latest
docker run -p 8002:8002 \
  -e NEO4J_URI=bolt://localhost:<TALOS_PORTS.neo4j_bolt> \
  -e NEO4J_USER=neo4j \
  -e NEO4J_PASSWORD=neo4jtest \
  -e MILVUS_HOST=localhost \
  -e MILVUS_PORT=<TALOS_PORTS.milvus_grpc> \
  ghcr.io/c-daly/talos:latest
```

## Simulated Hardware

### Sensors

```python
from talos.sensors import SimulatedCamera, SimulatedDepth, SimulatedIMU

camera = SimulatedCamera(resolution=(640, 480))
depth = SimulatedDepth(resolution=(320, 240))
imu = SimulatedIMU()

image = camera.read()
depth_map = depth.read()
acceleration, gyroscope = imu.read()
```

### Actuators

```python
from talos.actuators import SimulatedMotor, SimulatedGripper

motor = SimulatedMotor(name="arm_joint_1")
gripper = SimulatedGripper()

motor.set_position(45.0)
gripper.close()
```

## Pick-and-Place Scenario

```python
from talos.scenarios import PickAndPlaceScenario

scenario = PickAndPlaceScenario()
scenario.run()
```

## Integration Tests

```bash
./scripts/run_tests.sh integration
```

Uses port 57xxx range (from `logos_config.TALOS_PORTS`).

Environment overrides:
- `REUSE_EXISTING_STACK=1` - Skip docker compose up
- `KEEP_STACK_RUNNING=1` - Leave services running after tests

## CI Parity

```bash
poetry install --with dev
poetry run ruff check src tests
poetry run black --check src tests
poetry run mypy src
poetry run pytest --cov=talos --cov-report=term-missing --cov-fail-under=95
```

## Documentation

- [LOGOS Getting Started](https://github.com/c-daly/logos/blob/main/docs/guides/GETTING_STARTED.md)
- [Architecture Overview](https://github.com/c-daly/logos/blob/main/docs/architecture/ARCHITECTURE.md)
- [Testing Guide](https://github.com/c-daly/logos/blob/main/docs/guides/TESTING.md)

## License

MIT - see [LICENSE](LICENSE)
