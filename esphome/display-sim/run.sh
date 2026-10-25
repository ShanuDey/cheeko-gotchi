#!/usr/bin/env bash
# Runs the display simulator inside WSL (Ubuntu). Usage: ./run.sh [config|compile|run]   (default: run)
# The Linux venv and the build output stay in your WSL home, so the Windows .venv and .esphome are
# untouched. One-time setup: see README.md.
set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT="$HOME/.venvs/cgotchi"
export ESPHOME_DATA_DIR="$HOME/.esphome-sim"

cd "$(dirname "$0")"

# The simulator polls this file for changes (see display-sim.yaml).
[ -f settings.txt ] || cp settings.example.txt settings.txt
export DISPLAY_SIM_SETTINGS="$PWD/settings.txt"

uv sync --project ../..
exec uv run --project ../.. esphome "${1:-run}" display-sim.yaml
