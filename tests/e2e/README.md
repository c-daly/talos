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
        ├── docker-compose.test.yml  # Neo4j + Milvus test stack
        └── docker-compose.test.sophia.yml  # Optional Sophia stub service
```

## Stack Configuration

The test stack is **generated from LOGOS** using the `render-test-stacks` command. This ensures consistency across all repos.

### Services

Talos requires:
- **Neo4j** (host ports from `TALOS_PORTS`) - Knowledge graph storage
- **Milvus** (host ports from `TALOS_PORTS`) - Vector similarity search

### Port Allocation

Talos uses the 57xxx port range to avoid conflicts; host values are sourced
from `logos_config.TALOS_PORTS`.
| Service | Host Port (from `logos_config`) | Container Port |
|---------|----------------------------------|----------------|
| Neo4j HTTP | `TALOS_PORTS.neo4j_http` | Neo4j default HTTP |
| Neo4j Bolt | `TALOS_PORTS.neo4j_bolt` | Neo4j default Bolt |
| Milvus gRPC | `TALOS_PORTS.milvus_grpc` | Milvus default gRPC |
| Milvus Health | `TALOS_PORTS.milvus_metrics` | Milvus default health |

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
