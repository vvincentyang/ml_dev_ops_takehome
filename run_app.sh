#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
REQUESTED_PYTHON_BIN="${PYTHON_BIN:-}"
PYTHON_BIN=""
PYTHON_VERSION_CHECK='import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)'
INSTALL_INSTRUCTIONS=$'Python 3.12 or later is required.\n\nInstall options:\n- macOS with Homebrew: brew install python@3.12\n- Ubuntu/Debian: sudo apt-get update && sudo apt-get install python3.12 python3.12-venv\n- pyenv: pyenv install 3.12.10\n\nAfter installation, rerun this script or set PYTHON_BIN to the Python 3.12+ executable path.'


python_is_supported() {
  local candidate="$1"
  "${candidate}" -c "${PYTHON_VERSION_CHECK}" >/dev/null 2>&1
}


select_python_bin() {
  if [ -n "${REQUESTED_PYTHON_BIN}" ]; then
    if ! command -v "${REQUESTED_PYTHON_BIN}" >/dev/null 2>&1; then
      printf 'Configured PYTHON_BIN was not found: %s\n\n%s\n' "${REQUESTED_PYTHON_BIN}" "${INSTALL_INSTRUCTIONS}" >&2
      exit 1
    fi

    if ! python_is_supported "${REQUESTED_PYTHON_BIN}"; then
      printf 'Configured PYTHON_BIN does not satisfy Python 3.12+: %s\n\n%s\n' "${REQUESTED_PYTHON_BIN}" "${INSTALL_INSTRUCTIONS}" >&2
      exit 1
    fi

    PYTHON_BIN="${REQUESTED_PYTHON_BIN}"
    return
  fi

  for candidate in python3.13 python3.12 python3; do
    if command -v "${candidate}" >/dev/null 2>&1 && python_is_supported "${candidate}"; then
      PYTHON_BIN="${candidate}"
      return
    fi
  done

  printf 'No Python 3.12+ interpreter was found on PATH.\n\n%s\n' "${INSTALL_INSTRUCTIONS}" >&2
  exit 1
}


select_python_bin

if [ ! -d "${VENV_DIR}" ]; then
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "${PROJECT_ROOT}/requirements.txt"
python -c "from inference.assets import ensure_model_assets; ensure_model_assets()"

cd "${PROJECT_ROOT}"
exec python manage.py runserver "${HOST}:${PORT}"
