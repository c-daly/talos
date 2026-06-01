# CLAUDE.md — talos

## What This Is

Hardware abstraction layer for Project LOGOS. Provides simulated sensors, actuators, and
scenarios for Phase 1 development. Talos is a **library** (no API server) — other repos
import it or interact with it through sophia's executor layer.

Port 57000 is reserved for future API use. Infrastructure (Neo4j, Milvus) runs on shared
default ports.

## Dependencies

- **Python** >=3.12, **Poetry** for dependency management
- **logos-foundry** (v0.7.2) — shared config, HCG client, test utils
- **Neo4j** (7474/7687) — used by `executor/shim.py` for plan-step state
- **Milvus** (19530) — vector storage for sensor embedding tests
- **numpy** — sensor data generation (images, depth maps, IMU readings)
- **pydantic** — data models (e.g. `PlanNode` in executor)

## Key Commands

```bash
# Install
poetry install

# Lint & format
poetry run ruff check --fix .
poetry run ruff format .
poetry run black .
poetry run mypy src/

# Test
poetry run pytest                                    # all tests (60% coverage gate)
poetry run pytest tests/ -m unit                     # unit only (no services)
poetry run pytest tests/integration                  # needs Neo4j + Milvus running

# Helper scripts
bash scripts/test.sh                                 # run tests
bash scripts/lint.sh                                 # run linting
bash scripts/run_integration_stack.sh                # start infrastructure
```

## Architecture

```
src/talos/
├── sensors/
│   ├── base.py              # Sensor ABC — read(), enable/disable, get_info()
│   ├── camera.py            # SimulatedCamera — synthetic RGB images (numpy)
│   ├── depth.py             # SimulatedDepth — synthetic depth maps
│   └── imu.py               # SimulatedIMU — accelerometer + gyroscope data
├── actuators/
│   ├── base.py              # Actuator ABC — get_state(), enable/disable
│   ├── motor.py             # SimulatedMotor — position/velocity with clamping
│   └── gripper.py           # SimulatedGripper — open/close with grasp detection
├── executor/
│   └── shim.py              # ExecutorShim — applies PlanNode steps via Neo4j
├── scenarios/
│   └── pick_and_place.py    # PickAndPlaceScenario — full arm + gripper simulation
├── telemetry.py             # TelemetryRecorder — event logging for actuators
├── env.py                   # Environment helpers — Neo4j/Milvus config, repo root
├── fixtures.py              # Reusable pytest fixtures (mock_camera, mock_motor, etc.)
└── __init__.py              # Public API — re-exports all sensors, actuators, telemetry
```

### Key Abstractions

- **Sensor** (ABC): `read() -> Any`, enable/disable, `get_info()`. Concrete: Camera, Depth, IMU.
- **Actuator** (ABC): `get_state() -> dict`, enable/disable. Concrete: Motor (position/velocity), Gripper (open/close).
- **TelemetryRecorder**: Bounded event buffer (default 1000 events). Records position sets, grasp/release, errors.
- **ExecutorShim**: Connects to Neo4j, executes `PlanNode` steps (GRASP, RELEASE, MOVE_TO), updates graph state. Context manager for connection lifecycle.
- **PickAndPlaceScenario**: Composes 3 joints + gripper + all sensors. Methods: `move_to_object()`, `grasp_object()`, `release_object()`, `execute_pick_and_place()`.

### Test Layout

```
tests/
├── sensors/          # Unit tests per sensor type
├── actuators/        # Unit tests per actuator type
├── scenarios/        # Scenario composition, pick-and-place, executor loop
├── integration/      # Neo4j executor, Milvus embeddings, full sensor suite
└── (root)            # Telemetry, fixtures, env, actuator feedback
```

Test markers: `unit`, `integration`, `e2e`, `slow`.

## Conventions & Gotchas

- **Ruff** for linting, **black** for formatting (line-length 88, target py312)
- **mypy** with `disallow_untyped_defs = true` — all functions need type hints
- Sensors raise `RuntimeError` when read while disabled — always check `is_enabled()`
- Motors clamp position/velocity to configured limits silently (no error, just clamped)
- `ExecutorShim` is a context manager — use `async with` or call `__aenter__`/`__aexit__`
- Fixtures module (`fixtures.py`) uses try/except on import to avoid pytest dependency at runtime
- `env.py` resolution order: OS env vars > provided mapping > defaults
- Coverage threshold is **60%** (`--cov-fail-under=60` in pyproject.toml)
- Integration tests need Neo4j (7474/7687) and Milvus (19530) running locally

## Issue Templates

| Template | Use For |
|----------|---------|
| `task.yml` | Talos-specific development tasks |

Cross-repo templates (in `logos` repo): `infrastructure-task.yml`, `research-task.yml`, `documentation-task.yml`.
