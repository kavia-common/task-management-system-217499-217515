#!/usr/bin/env bash
set -euo pipefail

# Start the todo_database FastAPI service on 0.0.0.0:5001
# Ensures readiness for health checks via /healthz and full health at /api/health

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-5001}"

# Install dependencies if running in a pristine environment (optional safety)
# If pip is not desired at runtime, comment this out.
if command -v pip >/dev/null 2>&1 && [ -f "requirements.txt" ]; then
  pip install --no-input --no-cache-dir -r requirements.txt >/dev/null 2>&1 || true
fi

# Launch server
exec python -m uvicorn app:app --host "${HOST}" --port "${PORT}"
