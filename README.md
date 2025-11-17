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

```bash
pytest
```

### Code Formatting

```bash
black src/ tests/
ruff check src/ tests/
```

### Type Checking

```bash
mypy src/
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
