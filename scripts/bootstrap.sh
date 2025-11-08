#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${ROOT_DIR}/.venv"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "Python binary '${PYTHON_BIN}' not found. Set PYTHON_BIN to the desired interpreter." >&2
  exit 1
fi

PYTHON_VERSION="$("${PYTHON_BIN}" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
PYTHON_MAJOR_MINOR="$("${PYTHON_BIN}" -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')"

REQUIRED_MAJOR=3
REQUIRED_MINOR=12

if [[ "${PYTHON_MAJOR_MINOR%.*}" -lt "${REQUIRED_MAJOR}" ]] || { [[ "${PYTHON_MAJOR_MINOR%.*}" -eq "${REQUIRED_MAJOR}" ]] && [[ "${PYTHON_MAJOR_MINOR#*.}" -lt "${REQUIRED_MINOR}" ]]; }; then
  echo "Python ${REQUIRED_MAJOR}.${REQUIRED_MINOR}+ is required. Found ${PYTHON_VERSION}." >&2
  exit 1
fi

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "Creating virtual environment at ${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
else
  echo "Virtual environment already exists at ${VENV_DIR}"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

pip install --upgrade pip setuptools wheel >/dev/null

if command -v uv >/dev/null 2>&1; then
  echo "Installing project dependencies with uv"
  uv pip install --upgrade -e ".[dev]"
else
  echo "uv not found on PATH; falling back to pip"
  pip install --upgrade -e ".[dev]"
fi

echo "Environment bootstrap complete."
