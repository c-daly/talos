# Contributing to Talos

Thank you for your interest in contributing to Talos, the hardware abstraction layer for Project LOGOS!

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Poetry (recommended) or pip

### Setup with Poetry (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/c-daly/talos.git
   cd talos
   ```

2. Install dependencies:
   ```bash
   poetry install --with dev
   ```

3. Activate the virtual environment:
   ```bash
   poetry shell
   ```

### Setup with pip

1. Clone the repository:
   ```bash
   git clone https://github.com/c-daly/talos.git
   cd talos
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package in editable mode with development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## CI Parity: Running All Checks Locally

Before opening a pull request, run these commands to mirror the GitHub Actions CI pipeline:

```bash
poetry install --with dev
poetry run ruff check src tests
poetry run black --check src tests
poetry run mypy src
poetry run pytest --cov=talos --cov-report=term-missing --cov-report=xml --cov-fail-under=95
```

All checks must pass for your PR to be merged.

## Running Tests

With Poetry:
```bash
poetry run pytest
```

With pip:
```bash
pytest
```

For coverage reporting:
```bash
poetry run pytest --cov=talos --cov-report=term-missing
```

## Code Style

We use `black` for code formatting and `ruff` for linting.

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

## Type Checking

With Poetry:
```bash
poetry run mypy src/
```

With pip:
```bash
mypy src/
```

## Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linters
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Code of Conduct

Please be respectful and constructive in all interactions.

## Questions?

Open an issue or reach out to the Project LOGOS team.
