# Integration Testing with LOGOS Infrastructure

Talos integration tests use the shared LOGOS infrastructure for Neo4j and Milvus.

## Prerequisites

1. Start the LOGOS HCG development cluster:
```bash
# From the LOGOS root directory
cd /home/fearsidhe/projects/LOGOS/logos
docker compose -f infra/docker-compose.hcg.dev.yml up -d
```

2. Verify services are running:
```bash
docker compose -f infra/docker-compose.hcg.dev.yml ps
```

Expected services:
- `logos-hcg-neo4j` (ports 7474, 7687)
- `logos-hcg-milvus` (port 19530)

## Running Integration Tests

### Run All Tests (Unit + Integration)

```bash
cd /home/fearsidhe/projects/LOGOS/talos
poetry run pytest
```

### Run Only Unit Tests (No Infrastructure Required)

```bash
poetry run pytest -m "not integration"
```

### Run Only Integration Tests

```bash
poetry run pytest -m integration
```

### Run Specific Integration Test Files

```bash
# Neo4j executor tests
poetry run pytest tests/integration/test_executor_neo4j.py -v

# Milvus tests  
poetry run pytest tests/integration/test_milvus_comprehensive.py -v

# Sensor suite tests
poetry run pytest tests/integration/test_sensor_suite.py -v

# E2E scenario tests
poetry run pytest tests/integration/test_e2e_scenario.py -v
```

## Environment Variables

Integration tests use these environment variables (with defaults):

```bash
# Neo4j configuration
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="logosdev"

# Milvus configuration  
export MILVUS_HOST="localhost"
export MILVUS_PORT="19530"
```

## Test Behavior

Integration tests automatically skip if services are unavailable:

```
SKIPPED [1] tests/integration/test_executor_neo4j.py:45: Neo4j not available
```

This allows CI to run unit tests without requiring infrastructure.

## Coverage

Run tests with coverage:

```bash
poetry run pytest --cov=talos --cov-report=term-missing --cov-report=xml
```

Target coverage: **95%**

## Troubleshooting

### Tests Skip: "Neo4j not available"

1. Check Neo4j is running:
```bash
docker ps | grep neo4j
```

2. Test connection manually:
```bash
docker exec logos-hcg-neo4j cypher-shell -u neo4j -p logosdev "RETURN 1;"
```

### Tests Skip: "Milvus not available"

1. Check Milvus is running:
```bash
docker ps | grep milvus
```

2. Verify port is accessible:
```bash
nc -zv localhost 19530
```

### Clean Slate

To reset test data:

```bash
# Stop and remove volumes
docker compose -f /home/fearsidhe/projects/LOGOS/logos/infra/docker-compose.hcg.dev.yml down -v

# Restart fresh
docker compose -f /home/fearsidhe/projects/LOGOS/logos/infra/docker-compose.hcg.dev.yml up -d
```

## CI/CD

Integration tests are marked with `@pytest.mark.integration` and can be selectively run in CI pipelines.
