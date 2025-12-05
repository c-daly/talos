#!/usr/bin/env bash
set -euo pipefail

# Determine repo root: use TALOS_REPO_ROOT if set, otherwise compute from script location
if [[ -n "${TALOS_REPO_ROOT:-}" ]]; then
  REPO_ROOT="$TALOS_REPO_ROOT"
else
  REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
fi
DEFAULT_COMPOSE_FILE="$REPO_ROOT/tests/e2e/stack/talos/docker-compose.test.yml"
COMPOSE_CMD=${COMPOSE_CMD:-"docker compose"}
COMPOSE_FILE=${COMPOSE_FILE:-"$DEFAULT_COMPOSE_FILE"}
HEALTH_TIMEOUT=${HEALTH_TIMEOUT:-180}
# Talos-specific offsets (Neo4j 57xxx, Milvus 59xxx) to avoid clashes with other repos
PORTS_TO_CHECK=(
  "57474:Neo4j HTTP"
  "57687:Neo4j Bolt"
  "57530:Milvus gRPC"
  "57091:Milvus Metrics"
)
SERVICES=("neo4j" "milvus")
KEEP_STACK_RUNNING=${KEEP_STACK_RUNNING:-0}
REUSE_EXISTING_STACK=${REUSE_EXISTING_STACK:-0}
RUN_TESTS=${RUN_TESTS:-1}
PYTEST_BIN=${PYTEST_BIN:-"poetry run pytest"}
# shellcheck disable=SC2206
PYTEST_CMD=($PYTEST_BIN)

info() {
  echo "[info] $1"
}

warn() {
  echo "[warn] $1"
}

error() {
  echo "[error] $1" >&2
}

check_port_in_use() {
  local port=$1
  if command -v ss >/dev/null 2>&1; then
    if ss -tulpn 2>/dev/null | grep -q ":${port} "; then
      return 0
    fi
  elif command -v lsof >/dev/null 2>&1; then
    if lsof -i ":${port}" >/dev/null 2>&1; then
      return 0
    fi
  fi
  return 1
}

container_id() {
  local service=$1
  local id=""
  id=$($COMPOSE_CMD -f "$COMPOSE_FILE" ps -q "$service" 2>/dev/null | head -n1 || true)
  echo "$id"
}

container_display_name() {
  local container=$1
  local name=""
  name=$(docker inspect -f '{{.Name}}' "$container" 2>/dev/null | sed 's#^/##' || true)
  echo "${name:-$container}"
}

has_healthcheck() {
  local container=$1
  local hc=""
  hc=$(docker inspect -f '{{if .Config.Healthcheck}}true{{else}}false{{end}}' "$container" 2>/dev/null || true)
  [[ "$hc" == "true" ]]
}

wait_for_container() {
  local service=$1
  local container_id=$2
  local display_name=${3:-$2}
  local deadline=$((SECONDS + HEALTH_TIMEOUT))
  local expect_healthcheck=$4

  while (( SECONDS < deadline )); do
    local status=""
    status=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container_id" 2>/dev/null || true)

    case "$status" in
      healthy)
        info "$service ($display_name) is healthy"
        return 0
        ;;
      running)
        if [[ "$expect_healthcheck" == "false" ]]; then
          info "$service ($display_name) is running without healthcheck"
          return 0
        fi
        warn "$service ($display_name) is running but waiting for healthcheck"
        ;;
      unhealthy)
        error "$service ($display_name) reported unhealthy"
        docker logs "$container_id" --tail=200 || true
        return 1
        ;;
      starting|"" )
        info "$service ($display_name) still starting (status: ${status:-unknown})"
        ;;
      *)
        warn "$service ($display_name) status: $status"
        ;;
    esac
    sleep 5
  done

  error "$service ($display_name) did not become ready within ${HEALTH_TIMEOUT}s"
  docker logs "$container_id" --tail=200 || true
  return 1
}

cleanup() {
  if [[ "$REUSE_EXISTING_STACK" == "1" ]]; then
    return
  fi
  info "Stopping Talos integration services..."
  $COMPOSE_CMD -f "$COMPOSE_FILE" down >/dev/null 2>&1 || true
}

if [[ ! -f "$COMPOSE_FILE" ]]; then
  error "Compose file '$COMPOSE_FILE' not found. Override with COMPOSE_FILE=/path/to/docker-compose.hcg.dev.yml"
  exit 1
fi

if [[ "$REUSE_EXISTING_STACK" != "1" && "$KEEP_STACK_RUNNING" != "1" ]]; then
  trap cleanup EXIT
fi

if [[ "$REUSE_EXISTING_STACK" != "1" ]]; then
  info "Checking ports before starting services..."
  for mapping in "${PORTS_TO_CHECK[@]}"; do
    port=${mapping%%:*}
    label=${mapping#*:}
    if check_port_in_use "$port"; then
      warn "$label (port $port) already in use"
    else
      info "$label port $port is free"
    fi
  done

  info "Starting Neo4j + Milvus via $COMPOSE_CMD -f $COMPOSE_FILE"
  if ! $COMPOSE_CMD -f "$COMPOSE_FILE" up -d "${SERVICES[@]}"; then
    error "Failed to start services"
    $COMPOSE_CMD -f "$COMPOSE_FILE" logs --tail=200 || true
    exit 1
  fi
else
  info "Reusing existing stack defined in $COMPOSE_FILE"
fi

for service in "${SERVICES[@]}"; do
  container=$(container_id "$service")
  if [[ -z "$container" ]]; then
    error "Unable to determine container ID for '$service'"
    $COMPOSE_CMD -f "$COMPOSE_FILE" ps "$service" || true
    exit 1
  fi
  display_name=$(container_display_name "$container")
  if has_healthcheck "$container"; then
    expect_health="true"
  else
    expect_health="false"
  fi
  if ! wait_for_container "$service" "$container" "$display_name" "$expect_health"; then
    error "Aborting due to service failure: $service"
    exit 1
  fi
done

export NEO4J_URI=${NEO4J_URI:-"bolt://localhost:7687"}
export NEO4J_USERNAME=${NEO4J_USERNAME:-"neo4j"}
export NEO4J_PASSWORD=${NEO4J_PASSWORD:-"neo4jtest"}
export MILVUS_HOST=${MILVUS_HOST:-"localhost"}
export MILVUS_PORT=${MILVUS_PORT:-"19530"}

if [[ "$RUN_TESTS" == "0" ]]; then
  info "RUN_TESTS=0 set; skipping pytest execution"
  exit 0
fi

default_pytest_args=("-m" "integration" "-v")
if [[ $# -gt 0 ]]; then
  pytest_args=("$@")
else
  pytest_args=("${default_pytest_args[@]}")
fi

info "Running Talos integration tests: ${PYTEST_CMD[*]} ${pytest_args[*]}"
"${PYTEST_CMD[@]}" "${pytest_args[@]}"
