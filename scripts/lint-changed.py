#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path

MONO_ROOT = Path(__file__).parent.parent
BACKEND_DIR = MONO_ROOT / "IOPHA-backend"

def get_changed_files():
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "main...HEAD"],
            cwd=MONO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        files = [f for f in result.stdout.strip().split("\n") if f]
        return files
    except subprocess.CalledProcessError:
        print("No git changes detected, running on all backend files")
        return []

def main():
    changed_files = get_changed_files()
    
    python_files = [
        f for f in changed_files 
        if f.startswith("IOPHA-backend/") and f.endswith(".py")
    ]
    
    if not python_files:
        print("No Python files changed, skipping linting")
        return
    
    print(f"Running linting on {len(python_files)} changed Python file(s):")
    for f in python_files:
        print(f"  - {f}")
    
    full_paths = [MONO_ROOT / f for f in python_files]
    
    print("\nRunning Ruff check...")
    result = subprocess.run(
        ["ruff", "check"] + [str(p) for p in full_paths],
        cwd=BACKEND_DIR,
    )
    if result.returncode != 0:
        print("Ruff check failed")
        sys.exit(1)
    
    print("\nRunning Ruff format check...")
    result = subprocess.run(
        ["ruff", "format", "--check"] + [str(p) for p in full_paths],
        cwd=BACKEND_DIR,
    )
    if result.returncode != 0:
        print("Ruff format check failed")
        sys.exit(1)
    
    print("\nRunning Mypy...")
    result = subprocess.run(
        ["mypy"] + [str(p) for p in full_paths],
        cwd=BACKEND_DIR,
    )
    if result.returncode != 0:
        print("Mypy check failed")
        sys.exit(1)
    
    print("\nAll checks passed!")

if __name__ == "__main__":
    main()