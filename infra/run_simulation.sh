#!/usr/bin/env bash
# Run the infrastructure web UI (FastAPI + live canvas) in one step.
#
# Usage:
#   ./run_simulation.sh
#   PORT=8766 ./run_simulation.sh          # if 8765 is busy
#   TRAFFIC_VENV=/path/to/venv ./run_simulation.sh
#   ./run_simulation.sh --no-browser
#   ./run_simulation.sh --cli --steps 20   # terminal-only stub demo (no web)
#
# GVFS/SFTP paths contain ':' — do not create .venv inside the repo; use a venv
# under /tmp, ~/venvs, or set TRAFFIC_VENV.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

OPEN_BROWSER=1
CLI_MODE=0
CLI_STEPS=10

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-browser) OPEN_BROWSER=0; shift ;;
    --cli) CLI_MODE=1; shift ;;
    --steps)
      CLI_STEPS="${2:?}"
      shift 2
      ;;
    -h|--help)
      sed -n '1,20p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

resolve_venv() {
  if [[ -n "${TRAFFIC_VENV:-}" && -f "${TRAFFIC_VENV}/bin/activate" ]]; then
    echo "${TRAFFIC_VENV}"
    return 0
  fi
  if [[ -f /tmp/traffic-system-formal-venv/bin/activate ]]; then
    echo "/tmp/traffic-system-formal-venv"
    return 0
  fi
  if [[ -f "${HOME}/venvs/traffic-system-formal-venv/bin/activate" ]]; then
    echo "${HOME}/venvs/traffic-system-formal-venv"
    return 0
  fi
  return 1
}

if ! VENV_PATH="$(resolve_venv)"; then
  echo "No Python venv found for this project." >&2
  echo "" >&2
  echo "Create one on a path WITHOUT ':' (not inside some SFTP mount paths), e.g.:" >&2
  echo "  mkdir -p \"\${HOME}/venvs\"" >&2
  echo "  python3 -m venv \"\${HOME}/venvs/traffic-system-formal-venv\"" >&2
  echo "  source \"\${HOME}/venvs/traffic-system-formal-venv/bin/activate\"" >&2
  echo "  pip install -e \"${ROOT}[web]\"" >&2
  echo "" >&2
  echo "Then either export TRAFFIC_VENV to that path, or keep the venv at:" >&2
  echo "  /tmp/traffic-system-formal-venv" >&2
  exit 1
fi

# shellcheck source=/dev/null
source "${VENV_PATH}/bin/activate"

if [[ "$CLI_MODE" -eq 1 ]]; then
  echo "CLI stub demo (${CLI_STEPS} steps, no browser)…"
  exec python -m traffic_infra --steps "$CLI_STEPS"
fi

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8765}"

echo "Using venv: ${VENV_PATH}"
echo "Project:    ${ROOT}"
echo "Web UI:     http://${HOST}:${PORT}"
echo "Stop with Ctrl+C."
echo ""

if [[ "$OPEN_BROWSER" -eq 1 ]] && command -v xdg-open >/dev/null 2>&1 && [[ -n "${DISPLAY:-}" ]]; then
  (sleep 0.8 && xdg-open "http://${HOST}:${PORT}/") >/dev/null 2>&1 || true
fi

exec python -m traffic_infra.web_app --host "$HOST" --port "$PORT"
