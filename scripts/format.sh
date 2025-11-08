#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -d "${ROOT_DIR}/.venv" ]]; then
  echo "Virtual environment not found at ${ROOT_DIR}/.venv."
  echo "Run scripts/bootstrap.sh before formatting."
  exit 1
fi

# shellcheck disable=SC1091
source "${ROOT_DIR}/.venv/bin/activate"

black src tests
isort src tests

echo "Formatting complete."
