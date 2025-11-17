# Contributing to Talos

Thank you for your interest in contributing to Talos, the hardware abstraction layer for Project LOGOS!

## Development Setup

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

## Running Tests

```bash
pytest
```

## Code Style

We use `black` for code formatting and `ruff` for linting:

```bash
black src/ tests/
ruff check src/ tests/
```

## Type Checking

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
