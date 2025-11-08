#!/usr/bin/env bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "Virtual environment not found at ${VENV_DIR}."
  echo "Run scripts/bootstrap.sh first."
  exit 1
fi

shell_bin="${SHELL:-/bin/bash}"
echo "Activating virtual environment at ${VENV_DIR} using ${shell_bin}"
source "${VENV_DIR}/bin/activate"


