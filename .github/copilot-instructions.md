# Copilot Instructions — Talos

Short, practical guidance for AI coding agents working in `talos/` (hardware abstraction layer).

Big picture
- Talos provides hardware abstraction and simulated device interfaces used by Sophia and Apollo. For Phase 1 this repo typically exposes simulators and API shims rather than direct hardware drivers.

Key files & locations
- `pyproject.toml` / `README.md` — package metadata and quick start
- `docs/` — hardware capability docs and simulation guides
- `examples/` — simulation usage examples

Developer workflows
- Install dev deps: `pip install -e ".[dev]"` (run from `talos/`).
- Run simulation examples in `examples/` to validate hardware interfaces.
- Run tests: `pytest` — hardware-integration tests should be marked and run separately in CI environments configured with simulators.

Integration & patterns
- Talos exposes capabilities via APIs; do not attempt to modify the HCG directly from Talos. Use Sophia APIs for state changes.
- Provide deterministic simulation modes for CI and demo runs. Document the simulation flags/env vars in `docs/` and `README.md`.

GitHub, tickets & PRs
- Follow the workspace-wide rules in `logos/.github/copilot-instructions.md` for issues, labels, branch naming, and PR requirements. PRs that change simulated hardware interfaces must include example runs documented in `examples/`.
- When you pick up an issue on the LOGOS workspace project, move its card to *In Progress* (and update the `status/*` label). Move it to *Done* when the work lands so the shared project board stays accurate.

Examples
- Add a new simulator: place it under `examples/`, add unit tests, document CLI/start flags in `README.md`, and include a manual test step in the PR description.
