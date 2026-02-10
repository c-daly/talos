#!/usr/bin/env bash
# Run linters for Talos.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"
echo "Running ruff..."
poetry run ruff check .

echo "Running black..."
poetry run black --check .

echo "All checks passed."
