#!/usr/bin/env bash
# Talos all-tests runner (script parity with other repos).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"${SCRIPT_DIR}/run_tests.sh" all "$@"
