#!/usr/bin/env bash
set -euo pipefail

# Start uvicorn from the project root while making the project importable
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Ensure project root is on PYTHONPATH for module imports
export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"

# Run uvicorn with the project's Python interpreter (if available) to ensure dependencies are found
PYTHON_EXEC="$PROJECT_ROOT/venv/bin/python"
if [ ! -x "$PYTHON_EXEC" ]; then
    PYTHON_EXEC="python"
fi

exec "$PYTHON_EXEC" -m uvicorn backend.main:app "$@"
