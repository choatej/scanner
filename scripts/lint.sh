#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_BIN="${ROOT_DIR}/.venv/bin"

if [[ ! -d "${VENV_BIN}" ]]; then
  echo "Virtual environment not found at ${ROOT_DIR}/.venv."
  echo "Run scripts/bootstrap.sh before linting."
  exit 1
fi

# shellcheck disable=SC1091
source "${ROOT_DIR}/.venv/bin/activate"

black --check src tests
isort --check-only src tests
flake8 src tests
mypy src tests
bandit -r src
# TODO: create import-linter config file
#lint-imports

echo "All lint checks passed."
