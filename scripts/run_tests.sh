#!/usr/bin/env bash
# Talos Test Runner - Unified test management script
#
# Usage: ./scripts/run_tests.sh [command] [options]
#
# Commands:
#   unit        - Fast tests, no services needed
#   integration - Requires Neo4j + Milvus (starts services)
#   e2e         - Uses integration stack (Talos has no dedicated e2e suite yet)
#   all         - Run all tests
#
# Service commands:
#   up          - Start integration services
#   down        - Stop integration services
#   status      - Show service status
#   logs        - Show service logs

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

cd "${REPO_ROOT}"

resolve_default_ports() {
  python - <<'PY'
from logos_config.ports import get_repo_ports

ports = get_repo_ports("talos")
print(f"NEO4J_HTTP_PORT_DEFAULT={ports.neo4j_http}")
print(f"NEO4J_BOLT_PORT_DEFAULT={ports.neo4j_bolt}")
print(f"MILVUS_PORT_DEFAULT={ports.milvus_grpc}")
print(f"MILVUS_METRICS_PORT_DEFAULT={ports.milvus_metrics}")
PY
}

eval "$(resolve_default_ports)"

check_services() {
  if ! curl -s "http://localhost:${NEO4J_HTTP_PORT_DEFAULT}/" >/dev/null 2>&1; then
    return 1
  fi
  if ! curl -s "http://localhost:${MILVUS_METRICS_PORT_DEFAULT}/healthz" >/dev/null 2>&1; then
    return 1
  fi
  return 0
}

start_services() {
  RUN_TESTS=0 KEEP_STACK_RUNNING=1 "${SCRIPT_DIR}/run_integration_stack.sh"
}

stop_services() {
  COMPOSE_FILE="${REPO_ROOT}/tests/e2e/stack/talos/docker-compose.test.yml" \
    docker compose -f "${COMPOSE_FILE}" down
}

show_status() {
  COMPOSE_FILE="${REPO_ROOT}/tests/e2e/stack/talos/docker-compose.test.yml" \
    docker compose -f "${COMPOSE_FILE}" ps
}

show_logs() {
  COMPOSE_FILE="${REPO_ROOT}/tests/e2e/stack/talos/docker-compose.test.yml" \
    docker compose -f "${COMPOSE_FILE}" logs --tail=200
}

run_unit() {
  poetry run pytest tests/ -m "not integration" -v "$@"
}

run_integration() {
  if ! check_services; then
    echo -e "${YELLOW}Services not running. Starting them...${NC}"
    start_services
  fi
  poetry run pytest tests/integration/ -v "$@"
}

run_e2e() {
  echo -e "${YELLOW}Talos has no dedicated e2e suite yet; running integration tests.${NC}"
  run_integration "$@"
}

run_all() {
  if ! check_services; then
    echo -e "${YELLOW}Services not running. Starting them...${NC}"
    start_services
  fi
  poetry run pytest tests/ -v "$@"
}

case "${1:-help}" in
  unit|u)
    shift
    run_unit "$@"
    ;;
  integration|int|i)
    shift
    run_integration "$@"
    ;;
  e2e|end-to-end)
    shift
    run_e2e "$@"
    ;;
  all|a)
    shift
    run_all "$@"
    ;;
  up|start)
    start_services
    ;;
  down|stop)
    stop_services
    ;;
  status|st)
    show_status
    ;;
  logs|log)
    show_logs
    ;;
  help|--help|-h)
    echo -e "${CYAN}Talos Test Runner${NC}"
    echo "Usage: $0 <command> [pytest options]"
    ;;
  *)
    echo -e "${RED}Unknown command: $1${NC}"
    exit 1
    ;;
esac
