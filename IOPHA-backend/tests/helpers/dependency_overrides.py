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
        for key in overrides:
            app.dependency_overrides.pop(key, None)
        app.dependency_overrides.update(original_overrides)
