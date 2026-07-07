#!/usr/bin/env sh

# Resolve a working `ruff` invocation. It may be installed globally, inside a
# Python virtualenv, or runnable as a module. Without this the hook used to
# silently no-op when ruff was not on PATH.
resolve_ruff() {
  if command -v ruff >/dev/null 2>&1; then
    echo "ruff"
    return 0
  fi
  if [ -x venv/bin/ruff ]; then
    echo "venv/bin/ruff"
    return 0
  fi
  if command -v python3 >/dev/null 2>&1 && python3 -m ruff --version >/dev/null 2>&1; then
    echo "python3 -m ruff"
    return 0
  fi
  return 1
}
