#!/usr/bin/env bash
# Start local development environment for Talos.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

echo "Installing dependencies..."
poetry install --with dev

echo "Installing logos-foundry in editable mode (if local checkout exists)..."
if [[ -d "../logos" ]]; then
    poetry run pip install -e ../logos
fi

echo ""
echo "Talos dev environment ready."
echo "  Run tests:  ./scripts/test.sh"
echo "  Run lint:   ./scripts/lint.sh"
