# Agent Instructions

This guidance applies to the Talos repository and governs how AI agents interact with the codebase.

## Repository context

### Ecosystem overview
Talos is one of **five tightly coupled repositories** that compose the LOGOS cognitive architecture:

| Repo | Purpose |
|------|---------|
| **logos** | Foundry—canonical contracts, ontology, SDKs, shared tooling |
| **sophia** | Non-linguistic cognitive core (Orchestrator, CWM-A/G/E, Planner, Executor) |
| **hermes** | Stateless language & embedding utility (STT, TTS, NLP, embeddings) |
| **talos** (this repo) | Hardware abstraction layer for sensors/actuators |
| **apollo** | Thin client UI and command layer |

Talos provides the **hardware abstraction layer** for LOGOS. In Phase 1, it provides simulated interfaces for testing without physical hardware.

### This repository
Talos provides sensor and actuator abstractions:
- **Sensors** – Camera, depth, IMU (simulated in Phase 1)
- **Actuators** – Motors, grippers (simulated in Phase 1)
- **Scenarios** – Pre-configured simulations (e.g., pick and place)
- **Executor Shim** – Minimal executor for Sophia integration

Key directories:
- `src/talos/` – Core implementation
- `src/talos/sensors/` – Sensor abstractions and simulations
- `src/talos/actuators/` – Actuator abstractions and simulations
- `src/talos/scenarios/` – Simulation scenarios
- `tests/` – Unit and integration tests

### Key documentation
- `README.md` – Installation, architecture, features
- `CONTRIBUTING.md` – PR process and coding standards

---

## Communication and transparency

### Announce intent before acting
Do not take impactful actions—large refactors, dependency bumps, new features, API changes—without first describing your intent and waiting for acknowledgment. Explain *what* you plan to change and *why*.

### Surface uncertainty early
If a task is ambiguous, ask clarifying questions rather than guessing. When multiple reasonable interpretations exist, list them and ask which to pursue.

### No silent side effects
If your change will affect behavior, logging, error handling, or external APIs, call it out explicitly before proceeding.

---

## Workflow safety

### Never work directly on `main`
Always create a feature branch before making any changes. Branch naming convention:
```
<type>/<repo><issue-number>-<short-description>
```
Types: `feature/`, `fix/`, `refactor/`, `docs/`, `test/`, `chore/`

Examples:
```
feature/talos42-add-lidar-sensor
fix/talos123-imu-calibration
docs/talos15-sensor-api-docs
```

### Never push without a pull request
All changes—no matter how small—must go through a PR. Direct pushes to any shared branch are forbidden.

### Commit message format
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

Example:
```
feat(sensors): add simulated lidar sensor

Implements basic lidar point cloud simulation
for obstacle detection testing.

Part of c-daly/logos#421
```

---

## Code quality and professional practices

### Elevate code you touch
When modifying existing code, lift the surrounding area toward current best practices—improved typing, clearer error handling, better logging, more readable structure. Do not blindly copy nearby patterns that look stale or inconsistent.

### Small, composable functions
Prefer small, focused functions over monolithic blocks. Each function should do one thing well. Compose larger behaviors from smaller, testable units.

### Type hints and docstrings
Add or update type hints and docstrings whenever you introduce or modify public functions, classes, or methods. Prefer explicit types over `Any`.

### Backward compatibility
Maintain backward compatibility unless the task explicitly calls for a breaking change. If you must break compatibility, call it out clearly in your summary.

### Keep diffs minimal
Stay focused on the task. Avoid drive-by refactors, unrelated formatting changes, or scope creep. If you notice something worth fixing outside the current task, note it and suggest a follow-up ticket instead of bundling it in.

---

## Testing and linting

### Linting and formatting

All Python code must pass ruff and mypy before merge.

**Ruff** (linting + formatting):
```bash
# Check for issues
poetry run ruff check .

# Auto-fix what's possible
poetry run ruff check --fix .

# Format code
poetry run ruff format .

# Check formatting without changing files
poetry run ruff format --check .
```

**Mypy** (type checking):
```bash
poetry run mypy src/
```

**Pre-commit workflow**:
```bash
# Before committing, run:
poetry run ruff check --fix .
poetry run ruff format .
poetry run mypy src/
poetry run pytest tests/unit/
```

**Common issues and fixes**:
- `F401 imported but unused` → Remove the import or add `# noqa: F401` if re-exported
- `E501 line too long` → Ruff format usually fixes this; if not, break the line manually
- `I001 import order` → `ruff check --fix` will reorder imports
- Mypy `missing-imports` → Add type stubs or `# type: ignore[import-untyped]`

### Running tests
```bash
# Run all tests
poetry run pytest

# Run unit tests only
poetry run pytest tests/unit/

# Run integration tests (requires services)
poetry run pytest tests/integration/

# Run with coverage
poetry run pytest --cov=talos --cov-report=term
```

### Always note what you ran
In your summary, explicitly list which checks you executed. If none were run (e.g., documentation-only change), state that clearly.

---

## GitHub Access

You have full GitHub access through multiple methods. Use the appropriate one for your task.

### MCP Tools (preferred for simple operations)
Direct GitHub API access via MCP tools:
- `mcp_github_list_issues` / `mcp_github_search_issues` – Find issues
- `mcp_github_issue_write` – Create/update issues
- `mcp_github_create_pull_request` – Open PRs
- `mcp_github_pull_request_read` – Get PR details, diffs, status
- `mcp_github_list_commits` / `mcp_github_get_commit` – View commits

### GitHub CLI (for complex queries)
```bash
# Issues
gh issue list --repo c-daly/talos
gh issue create --title "..." --body "..."
gh issue view 123

# Pull requests
gh pr list --repo c-daly/talos
gh pr create --title "..." --body "..." --base main
gh pr view 123
gh pr checks 123
```

### Cross-repo references
When referencing issues/PRs in other repos, use full format:
```
Part of c-daly/logos#421
Fixes c-daly/sophia#64
```

---

## Pull request and summary expectations

### PR title format
```
<type>(<scope>): <description>
```

### PR description template
```markdown
## Summary
Brief description of changes.

## Changes
- Change 1
- Change 2

## Testing
How this was tested.

## Related Issues
Part of c-daly/logos#XXX
```

### Completion summary
At the end of every session, provide a summary that includes:
1. **What was changed** – Files created, modified, or deleted
2. **Why** – The problem solved or feature added
3. **What was tested** – Commands executed and their outcomes
4. **What's next** – Any follow-up tasks or known issues

---

## Quick reference

| Task | Command |
|------|---------|
| Install deps | `poetry install` |
| Run linting | `poetry run ruff check .` |
| Auto-fix lint | `poetry run ruff check --fix .` |
| Format code | `poetry run ruff format .` |
| Type check | `poetry run mypy src/` |
| Run all tests | `poetry run pytest` |
| Run unit tests | `poetry run pytest tests/unit/` |

### Ecosystem standards
| Document | Location |
|----------|----------|
| Testing standards | `logos/docs/TESTING_STANDARDS.md` |
| Git/project standards | `logos/docs/GIT_PROJECT_STANDARDS.md` |
