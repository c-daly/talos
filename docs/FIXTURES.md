# Mock Hardware Fixtures Documentation

This document provides comprehensive documentation for Talos mock hardware fixtures, designed for Phase 1 testing with simulated devices.

## Overview

Talos provides pytest fixtures that encapsulate simulated hardware components, making it easy to write tests for robotic scenarios without requiring physical hardware. These fixtures are designed to be consumed by:

- Sophia's cognitive architecture test harness
- Talos internal tests
- External projects requiring hardware simulation

## Installation and Setup

### In Your Test Suite

Add to your `conftest.py`:

```python
pytest_plugins = ["talos.fixtures"]
```

Or import fixtures directly in test files:

```python
from talos.fixtures import mock_camera, mock_pick_and_place
```

See `docs/FIXTURES.md` for comprehensive fixture documentation.
