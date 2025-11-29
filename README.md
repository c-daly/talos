# Talos

Talos: Sensor/Actuator Abstraction Layer for Project LOGOS

[![CI](https://github.com/c-daly/talos/actions/workflows/ci.yml/badge.svg)](https://github.com/c-daly/talos/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Talos is the hardware abstraction layer for Project LOGOS, providing a unified interface for sensors and actuators. In Phase 1, Talos provides simulated interfaces for testing and development of the cognitive architecture without requiring physical hardware.

## Purpose

- Abstract sensor/actuator hardware behind clean Python interfaces
- Provide simulated sensors (camera, depth, IMU) for Phase 1 development
- Provide simulated actuators (motors, grippers) for Phase 1 development
- Enable "pick and place" scenario simulation for testing Sophia's planning capabilities
- Support future integration with real hardware in later phases

## Architecture

Talos defines abstract base classes for sensors and actuators, with concrete implementations for simulation:

```
talos/
├── sensors/          # Sensor abstractions and implementations
│   ├── base.py       # Sensor base class
│   ├── camera.py     # Simulated camera
│   ├── depth.py      # Simulated depth sensor
│   └── imu.py        # Simulated IMU (Inertial Measurement Unit)
├── actuators/        # Actuator abstractions and implementations
│   ├── base.py       # Actuator base class
│   ├── motor.py      # Simulated motor
│   └── gripper.py    # Simulated gripper
├── scenarios/        # Pre-configured scenarios
│   └── pick_and_place.py  # Pick and place simulation
└── executor/         # Executor shim for Sophia integration
    └── shim.py       # Minimal executor that applies plan steps to Neo4j
```

#### Integration Tests

Talos includes integration tests for external services like Milvus (vector database) and Neo4j. These tests validate:

- Milvus collection initialization and configuration
- Embedding storage and retrieval via sync utilities (simulating Hermes)
- Metadata/UUID verification in Neo4j
- Health checks and collection count assertions

Use the shared helper to bring up the LOGOS stack, wait for health, and run `pytest` in one step:

```bash
cd /home/fearsidhe/projects/LOGOS/talos
./scripts/run_integration_stack.sh                # defaults to pytest -m integration -v
./scripts/run_integration_stack.sh tests/integration/test_executor_neo4j.py -v
```

Key environment overrides:

- `COMPOSE_FILE` – path to the LOGOS docker compose file (defaults to `../logos/infra/docker-compose.hcg.dev.yml`).
- `REUSE_EXISTING_STACK=1` – skip `docker compose up` if you already have the stack running.
- `KEEP_STACK_RUNNING=1` – leave services up after pytest completes.
- `NEO4J_*` / `MILVUS_*` – override connection info used by the tests.

If you prefer bringing up services manually, ensure Neo4j and Milvus are running (see `docs/INTEGRATION_TESTING.md`) and then:

```bash
poetry run pytest -m integration
```

To target a specific file or test, pass the usual pytest arguments either directly to `run_integration_stack.sh` or to `poetry run pytest` if the stack is already running.
   # Option 1: Spawn a shell within the virtual environment
   poetry shell
   
   # Option 2: Run commands with 'poetry run'
   poetry run python examples/sensor_example.py
   ```

### Using Docker

The recommended way to run Talos is using the pre-built Docker image:

```bash
# Pull the latest image
docker pull ghcr.io/c-daly/talos:latest

# Run with environment variables
docker run -p 8002:8002 \
  -e NEO4J_URI=bolt://your-neo4j-host:7687 \
  -e NEO4J_USER=neo4j \
  -e NEO4J_PASSWORD=your-password \
  -e MILVUS_HOST=your-milvus-host \
  -e MILVUS_PORT=19530 \
  ghcr.io/c-daly/talos:latest
```

### Installing with pip

If you prefer using pip:

```bash
# Clone the repository
git clone https://github.com/c-daly/talos.git
cd talos

# Install in development mode
pip install -e ".[dev]"
```

## Local Testing (CI Parity)

Talos also consumes the shared LOGOS workflow template. Mirror the GitHub Actions job locally with:

```bash
poetry install --with dev
poetry run ruff check src tests
poetry run black --check src tests
poetry run mypy src
poetry run pytest --cov=talos --cov-report=term-missing --cov-report=xml --cov-fail-under=95
```

Running these commands before opening a pull request ensures parity with `.github/workflows/ci.yml`.

## Quick Start

### Using Simulated Sensors

```python
from talos.sensors import SimulatedCamera, SimulatedDepth, SimulatedIMU

# Create sensors
camera = SimulatedCamera(resolution=(640, 480))
depth = SimulatedDepth(resolution=(320, 240))
imu = SimulatedIMU()

# Read sensor data
image = camera.read()
depth_map = depth.read()
acceleration, gyroscope = imu.read()
```

### Using Simulated Actuators

```python
from talos.actuators import SimulatedMotor, SimulatedGripper

# Create actuators
motor = SimulatedMotor(name="arm_joint_1")
gripper = SimulatedGripper()

# Control actuators
motor.set_position(1.57)  # radians
gripper.open()
gripper.close()
```

### Using Telemetry

```python
from talos.actuators import SimulatedMotor, SimulatedGripper
from talos.telemetry import TelemetryRecorder, EventType

# Create shared telemetry recorder
telemetry = TelemetryRecorder(max_events=1000)

# Create actuators with telemetry
motor = SimulatedMotor(name="arm_joint_1", telemetry=telemetry)
gripper = SimulatedGripper(name="gripper", telemetry=telemetry)

# Perform operations
motor.set_position(1.57)
gripper.close()
gripper.grasp("cup")

# Query telemetry
events = telemetry.get_events(actuator_name="gripper")
position_events = telemetry.get_events(event_type=EventType.POSITION_SET)

# Export telemetry data
telemetry_data = telemetry.to_dict()
```

### Pick and Place Scenario

```python
from talos.scenarios import PickAndPlaceScenario

# Create scenario
scenario = PickAndPlaceScenario()

# Get initial state
state = scenario.get_state()

# Execute actions
scenario.move_to_object("cup")
scenario.grasp_object("cup")
scenario.move_to_location("table")
scenario.release_object()

# Access telemetry
telemetry_events = scenario.telemetry.get_events()
```

### Executor Shim (M4 Integration)

The executor shim simulates the Talos/Executor loop by consuming plan nodes and applying state changes to Neo4j, representing Talos action feedback:

```python
from talos.executor import ExecutorShim, PlanNode, ActionType

# Create executor shim (requires Neo4j)
with ExecutorShim(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="password"
) as executor:
    # Execute a grasp action
    grasp_node = PlanNode(
        node_id="plan_001",
        action_type=ActionType.GRASP,
        target="cup"
    )
    result = executor.execute_plan_node(grasp_node)
    
    # Query object state
    state = executor.get_object_state("cup")
    print(f"Cup grasped: {state['grasped']}")
    
    # Execute a move action
    move_node = PlanNode(
        node_id="plan_002",
        action_type=ActionType.MOVE_TO,
        target="shelf",
        parameters={"position": [0.3, 0.2, 0.3]}
    )
    executor.execute_plan_node(move_node)
    
    # Query robot location
    location = executor.get_robot_location()
```

See `examples/executor_example.py` for a complete example and `tests/scenarios/test_m4_executor_loop.py` for tests using a mock Neo4j driver.

## Development

### Installing for Development

To set up Talos for development, you need to install it in editable mode along with development dependencies.

#### With Poetry (Recommended)

Poetry automatically handles editable installs and development dependencies:

```bash
# Install all dependencies including dev dependencies
poetry install --with dev

# Or if you already have the main dependencies:
poetry install

# Activate the virtual environment
poetry shell
```

#### With pip

When using pip, you need to explicitly install in editable mode:

```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# This installs the package in development mode, allowing you to
# modify the source code without reinstalling
```

**Important**: If you don't install in editable mode (using `-e` flag or `poetry install`), you'll need to set the `PYTHONPATH` environment variable to use the local source code:

```bash
# Only needed if NOT installed in editable mode
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Or for a single command:
PYTHONPATH=src pytest
```

### Running Tests

#### Basic Test Execution

With Poetry:
```bash
poetry run pytest
```

With pip (after editable install):
```bash
pytest
```

#### Running Tests with Coverage

To run tests with coverage reporting:

```bash
# With Poetry
poetry run pytest --cov=talos --cov-report=term-missing

# With pip
pytest --cov=talos --cov-report=term-missing
```

#### Integration Tests

Talos includes integration tests for external services like Milvus (vector database) and Neo4j. These tests validate:

- Milvus collection initialization and configuration
- Embedding storage and retrieval via sync utilities (simulating Hermes)
- Metadata/UUID verification in Neo4j
- Health checks and collection count assertions

Integration tests are designed to skip gracefully when external services are unavailable, with clear messages explaining why they were skipped. Run all tests including integration tests with:

```bash
pytest tests/
```

Or run only integration tests:

```bash
pytest tests/integration/
```

#### Coverage Requirements

This project enforces a minimum coverage threshold of **95%**. The CI pipeline will fail if coverage drops below this threshold.

To check coverage and fail if below threshold:

```bash
# With Poetry
poetry run pytest --cov=talos --cov-report=term-missing --cov-fail-under=95

# With pip
pytest --cov=talos --cov-report=term-missing --cov-fail-under=95
```

To generate an XML coverage report (used by Codecov):

```bash
pytest --cov=talos --cov-report=xml
```

### Code Formatting

With Poetry:
```bash
poetry run black src/ tests/
poetry run ruff check src/ tests/
```

With pip:
```bash
black src/ tests/
ruff check src/ tests/
```

### Type Checking

With Poetry:
```bash
poetry run mypy src/
```

With pip:
```bash
mypy src/
```

### Running All Checks

To run all quality checks (linting, formatting, type checking, and tests):

```bash
# With Poetry
poetry run ruff check src/ tests/
poetry run black --check src/ tests/
poetry run mypy src/
poetry run pytest --cov=talos --cov-report=term-missing --cov-fail-under=95

# With pip
ruff check src/ tests/
black --check src/ tests/
mypy src/
pytest --cov=talos --cov-report=term-missing --cov-fail-under=95
```

### Continuous Integration

This project uses GitHub Actions for CI/CD. On every pull request and push to `main`, the following checks are run:

- **Linting**: `ruff check src/ tests/`
- **Formatting**: `black --check src/ tests/`
- **Type Checking**: `mypy src/`
- **Tests with Coverage**: `pytest --cov=talos --cov-report=xml --cov-fail-under=95`
- **Coverage Upload**: Results are uploaded to Codecov

All checks must pass before code can be merged.

### Adding Dependencies

To add a new dependency with Poetry:
```bash
# Production dependency
poetry add package-name

# Development dependency
poetry add --group dev package-name
```

### Updating Dependencies

```bash
# Update all dependencies
poetry update

# Update a specific package
poetry update package-name
```

## Testing with Mock Hardware Fixtures

Talos provides pytest fixtures for easy testing of robotic scenarios. These fixtures are designed to be consumed by Sophia's test harness and other testing frameworks.

### Available Fixtures

- `mock_camera` - Simulated camera sensor
- `mock_depth_sensor` - Simulated depth sensor
- `mock_imu` - Simulated IMU
- `mock_motor` - Simulated motor actuator
- `mock_gripper` - Simulated gripper actuator
- `mock_telemetry` - Telemetry recorder for tracking operations
- `mock_pick_and_place` - Complete pick-and-place scenario
- `mock_robot_arm` - Multi-joint robot arm (3 joints)
- `mock_sensor_suite` - Complete suite of sensors

### Using Fixtures in Tests

Add this to your `conftest.py`:

```python
pytest_plugins = ["talos.fixtures"]
```

Then use fixtures in your tests:

```python
def test_robot_operation(mock_pick_and_place):
    """Test a pick and place operation."""
    scenario = mock_pick_and_place
    
    # Execute operation
    success, actions = scenario.execute_pick_and_place("cup", "shelf")
    
    assert success
    assert len(actions) == 4
    
    # Access telemetry
    events = scenario.telemetry.get_events()
    assert len(events) > 0
```

See `examples/fixtures_example.py` for more examples.

## Phase 1 Deliverables

- [x] Python project structure
- [x] Sensor interface abstractions
- [x] Actuator interface abstractions
- [x] Simulated camera sensor
- [x] Simulated depth sensor
- [x] Simulated IMU sensor
- [x] Simulated motor actuator
- [x] Simulated gripper actuator
- [x] Pick and place scenario simulation
- [x] Unit tests
- [x] Integration tests
- [x] Milvus embedding integration smoke test
- [x] Mock hardware fixtures for testing
- [x] Executor shim for M4 integration (Talos/Executor loop simulation)

## Related Repositories

- [c-daly/logos](https://github.com/c-daly/logos) — Meta-repository with specs and HCG infrastructure
- [c-daly/sophia](https://github.com/c-daly/sophia) — Cognitive core (Orchestrator, CWM, Planner, Executor)
- [c-daly/hermes](https://github.com/c-daly/hermes) — Language & embedding utilities
- [c-daly/apollo](https://github.com/c-daly/apollo) — UI and command interface

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.
