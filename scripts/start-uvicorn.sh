#!/usr/bin/env bash
set -euo pipefail

# Start uvicorn from the project root while making the project importable
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Ensure project root is on PYTHONPATH for module imports
export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:}$PYTHONPATH"

# Run uvicorn with any args passed through
exec uvicorn backend.main:app "$@"
