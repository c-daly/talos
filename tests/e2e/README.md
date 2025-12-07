# End-to-End Tests

This directory contains Talos's end-to-end (e2e) integration tests and their supporting infrastructure.

## Directory Structure

```
tests/e2e/
├── README.md           # This file
└── stack/
    └── talos/
        ├── .env.test           # Environment variables for the stack
        ├── STACK_VERSION       # Git commit hash of logos that generated these files
        └── docker-compose.test.yml  # Neo4j + Milvus test stack
```

## Stack Configuration

The test stack is **generated from LOGOS** using the `render-test-stacks` command. This ensures consistency across all repos.

### Services

Talos requires:
- **Neo4j** (ports 57474/57687) - Knowledge graph storage
- **Milvus** (ports 57530/57091) - Vector similarity search

### Port Allocation

Talos uses the 57xxx port range to avoid conflicts:
| Service | Host Port | Container Port |
|---------|-----------|----------------|
| Neo4j HTTP | 57474 | 7474 |
| Neo4j Bolt | 57687 | 7687 |
| Milvus gRPC | 57530 | 19530 |
| Milvus Health | 57091 | 9091 |

## Running Integration Tests

### Using the Helper Script

```bash
# Run all integration tests
./scripts/run_integration_stack.sh

# Run specific tests
./scripts/run_integration_stack.sh tests/integration/test_specific.py -v
```

The script will:
1. Start the Neo4j + Milvus stack
2. Wait for all services to be healthy
3. Run pytest with the specified arguments
4. Clean up containers on exit

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TALOS_REPO_ROOT` | Override repo root detection | Auto-detected |
| `HEALTH_TIMEOUT` | Seconds to wait for services | 180 |
| `COMPOSE_CMD` | Docker compose command | `docker compose` |

## Regenerating Stack Files

If you need to update the stack configuration:

```bash
# From the LOGOS repo
cd /path/to/logos
poetry run render-test-stacks --repo talos

# Copy the generated files to talos
cp tests/e2e/stack/talos/* /path/to/talos/tests/e2e/stack/talos/
```

The `STACK_VERSION` file contains the LOGOS commit hash used to generate the files.
