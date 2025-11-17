# Talos

Talos: Sensor/Actuator Abstraction Layer for Project LOGOS

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
└── scenarios/        # Pre-configured scenarios
    └── pick_and_place.py  # Pick and place simulation
```

## Installation

### Prerequisites

- Python 3.11 or higher
- Poetry (recommended) or pip

### Installing with Poetry (Recommended)

Poetry provides better dependency management and reproducible builds.

1. **Install Poetry** (if not already installed):
   ```bash
   # Via pip
   pip install poetry
   
   # Or via the official installer (recommended)
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Clone the repository**:
   ```bash
   git clone https://github.com/c-daly/talos.git
   cd talos
   ```

3. **Install dependencies**:
   ```bash
   # Install all dependencies (including dev dependencies)
   poetry install
   
   # Or install only production dependencies
   poetry install --without dev
   ```

4. **Activate the virtual environment**:
   ```bash
   # Option 1: Spawn a shell within the virtual environment
   poetry shell
   
   # Option 2: Run commands with 'poetry run'
   poetry run python examples/sensor_example.py
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
```

## Development

### Running Tests

With Poetry:
```bash
poetry run pytest
```

With pip:
```bash
pytest
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

## Related Repositories

- [c-daly/logos](https://github.com/c-daly/logos) — Meta-repository with specs and HCG infrastructure
- [c-daly/sophia](https://github.com/c-daly/sophia) — Cognitive core (Orchestrator, CWM, Planner, Executor)
- [c-daly/hermes](https://github.com/c-daly/hermes) — Language & embedding utilities
- [c-daly/apollo](https://github.com/c-daly/apollo) — UI and command interface

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.
