#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
if [[ ! -x "$ROOT/backend/.venv/bin/python" ]]; then
  echo "Create backend/.venv and install backend/requirements.txt first." >&2; exit 1
fi
if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
  echo "Run npm install in frontend first." >&2; exit 1
fi
cd "$ROOT/backend"
"$ROOT/backend/.venv/bin/python" -m uvicorn app.main:app --reload --port 8137 & BACK_PID=$!
cd "$ROOT/frontend"
export VITE_API_URL="${VITE_API_URL:-http://127.0.0.1:8137/api}"
npm run dev & FRONT_PID=$!
trap 'kill "$BACK_PID" "$FRONT_PID" 2>/dev/null || true' EXIT INT TERM
wait
