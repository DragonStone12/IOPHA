from contextlib import contextmanager
from typing import Generator

from fastapi import FastAPI


@contextmanager
def override_dependencies(app: FastAPI, overrides: dict) -> Generator[None, None, None]:
    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides.update(overrides)
    try:
        yield
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)
