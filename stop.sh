#!/usr/bin/env zsh
echo "[Autoforge AI] Stopping server on port 8000..."
PIDS=$(lsof -ti :8000)
if [ -n "$PIDS" ]; then
    kill -9 $PIDS
    echo "[Autoforge AI] Server stopped."
else
    echo "[Autoforge AI] No server is currently running on port 8000."
fi

