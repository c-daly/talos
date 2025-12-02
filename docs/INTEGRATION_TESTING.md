# Integration Testing with LOGOS Infrastructure

Talos integration tests depend on the shared LOGOS HCG stack (Neo4j + Milvus). The
repository now ships a helper script that mirrors the workflow used in Sophia and
Hermes so contributors do not have to memorize Docker commands.

## Recommended Workflow: `scripts/run_integration_stack.sh`

```bash
cd /home/fearsidhe/projects/LOGOS/talos
./scripts/run_integration_stack.sh                # starts stack + runs pytest -m integration -v
./scripts/run_integration_stack.sh tests/integration/test_executor_neo4j.py -k grasp
```

The helper:

1. Checks for port conflicts on 7474/7687/19530/9091 before starting services.
2. Uses `docker compose ps -q` to locate the actual container IDs from
	 `../logos/infra/docker-compose.hcg.dev.yml` (override with `COMPOSE_FILE`).
3. Polls health (Neo4j) or running state (Milvus) with log tailing on failure.
4. Exports the expected `NEO4J_*` / `MILVUS_*` variables, then runs pytest.

### Environment Overrides

| Variable | Description |
| --- | --- |
| `COMPOSE_FILE` | Path to the compose file (defaults to `../logos/infra/docker-compose.hcg.dev.yml`). |
| `COMPOSE_CMD` | Change the compose binary, e.g. `COMPOSE_CMD="docker compose --project-name logos-hcg"`. |
| `HEALTH_TIMEOUT` | Seconds to wait for each service before failing (default 180). |
| `REUSE_EXISTING_STACK=1` | Skip `docker compose up`; assumes the stack is already running. |
| `KEEP_STACK_RUNNING=1` | Leave services running after pytest completes. |
| `RUN_TESTS=0` | Start the stack (and optionally keep it up) without invoking pytest. |
| `PYTEST_BIN` | Override the pytest command (default `poetry run pytest`). |
| `TALOS_REPO_ROOT` | Override automatic detection of the repository root (used by tests and scripts). |
| `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` | Connection info passed to tests. |
| `MILVUS_HOST`, `MILVUS_PORT` | Milvus connection info (defaults to `localhost`/`19530`). |

Examples:

```bash
# Keep services running for manual debugging
KEEP_STACK_RUNNING=1 ./scripts/run_integration_stack.sh

# Reuse an existing stack and only run a subset of tests
REUSE_EXISTING_STACK=1 ./scripts/run_integration_stack.sh tests/integration/test_milvus_comprehensive.py -k metadata

# Bring up services but skip pytest (useful for local dev shells)
RUN_TESTS=0 KEEP_STACK_RUNNING=1 ./scripts/run_integration_stack.sh
```

## Manual Workflow (Fallback)

If you cannot use the helper, bring up the stack manually from the `logos` repo:

```bash
cd /home/fearsidhe/projects/LOGOS/logos
docker compose -f infra/docker-compose.hcg.dev.yml up -d neo4j milvus-standalone
docker compose -f infra/docker-compose.hcg.dev.yml ps
```

Expected services:
- `logos-hcg-neo4j` (ports 7474, 7687)
- `logos-hcg-milvus` (ports 19530, 9091)

Then, from the Talos repository:

```bash
# Run unit + integration tests
poetry run pytest

# Only integration tests
poetry run pytest -m integration

# Targeted files
poetry run pytest tests/integration/test_executor_neo4j.py -v
poetry run pytest tests/integration/test_milvus_comprehensive.py -v
poetry run pytest tests/integration/test_sensor_suite.py -v
poetry run pytest tests/integration/test_e2e_scenario.py -v
```

## Test Behavior & Coverage

- Tests marked `@pytest.mark.integration` automatically skip when services are unavailable.
- Default environment variables:

	```bash
	export NEO4J_URI="bolt://localhost:7687"
	export NEO4J_USERNAME="neo4j"
	export NEO4J_PASSWORD="neo4jtest"
	export MILVUS_HOST="localhost"
	export MILVUS_PORT="19530"
	```

- CI enforces **95%** coverage:

	```bash
	poetry run pytest --cov=talos --cov-report=term-missing --cov-report=xml
	```

## Troubleshooting

### Script exits early

- Port conflicts: the helper prints a warning. Stop the conflicting process or set
	`REUSE_EXISTING_STACK=1` if you intentionally started a custom stack.
- Health timeout: inspect the streamed logs printed by the script, then rerun.

### Tests Skip: "Neo4j not available"

```bash
docker ps | grep neo4j
docker exec logos-hcg-neo4j cypher-shell -u neo4j -p neo4jtest "RETURN 1;"
```

### Tests Skip: "Milvus not available"

```bash
docker ps | grep milvus
nc -zv localhost 19530
```

### Clean Slate

```bash
docker compose -f /home/fearsidhe/projects/LOGOS/logos/infra/docker-compose.hcg.dev.yml down -v
docker compose -f /home/fearsidhe/projects/LOGOS/logos/infra/docker-compose.hcg.dev.yml up -d
```

## CI/CD

Integration tests are marked with `@pytest.mark.integration` and can be selectively run
in CI pipelines. Use the helper locally to match CI expectations before opening a PR.
