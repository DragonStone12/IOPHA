#!/usr/bin/env sh

# Resolve a working `ruff` invocation from the project virtualenv only.
# Hooks must use the project venv so all dependencies (and their versions) are
# controlled by the repository; global or Anaconda installations are not used.
resolve_ruff() {
  if [ -x IOPHA-backend/venv/bin/ruff ]; then
    echo "IOPHA-backend/venv/bin/ruff"
    return 0
  fi
  if [ -x venv/bin/ruff ]; then
    echo "venv/bin/ruff"
    return 0
  fi
  return 1
}
