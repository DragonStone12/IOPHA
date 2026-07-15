#!/bin/sh

if [ -x "IOPHA-backend/venv/bin/ruff" ]; then
  echo "IOPHA-backend/venv/bin/ruff"
  exit 0
fi

if command -v ruff >/dev/null 2>&1; then
  echo "ruff"
  exit 0
fi

if command -v python3 >/dev/null 2>&1 && python3 -m ruff --version >/dev/null 2>&1; then
  echo "python3 -m ruff"
  exit 0
fi

echo "Error: ruff not found" >&2
exit 1
