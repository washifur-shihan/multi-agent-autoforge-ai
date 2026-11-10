#!/usr/bin/env zsh
set -e

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "[Autoforge AI] Creating virtual environment (.venv)..."
    python3 -m venv .venv
    ./.venv/bin/pip install -r requirements.txt
fi

echo "[Autoforge AI] Starting server at http://localhost:8000 ..."
exec ./.venv/bin/python api.py
