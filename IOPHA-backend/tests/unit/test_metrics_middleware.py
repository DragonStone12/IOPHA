import json
from typing import Any

import pytest
from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics.provider import cold_start
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

import app.main as main_module
from app.core.config import settings
from app.main import app
from app.middleware.metrics import (
    UNMATCHED_ROUTE,
    MetricsMiddleware,
    resolve_route_template,
    sanitize_route_template,
    status_class,
)


def _emf_blobs(capsys: pytest.CaptureFixture[str]) -> list[dict[str, Any]]:
    """Parse every EMF JSON blob (objects carrying ``_aws``) from stdout."""
    blobs: list[dict[str, Any]] = []
    for line in capsys.readouterr().out.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "_aws" in payload:
            blobs.append(payload)
    return blobs


def _make_app(metrics_enabled: bool = True) -> FastAPI:
    isolated = FastAPI()
    isolated.add_middleware(
        MetricsMiddleware,
        metrics=Metrics(namespace="Test/Namespace", service="test-service"),
    )

    @isolated.get("/ok/{item_id}")
    def ok(item_id: str) -> dict[str, str]:
        return {"item": item_id}

    @isolated.get("/boom")
    def boom() -> None:
        raise RuntimeError("kaboom")

    return isolated


def test_emf_blob_emitted_per_request_with_core_metrics(
    capsys: pytest.CaptureFixture[str],
) -> None:
    response = TestClient(app).get("/api/health")

    assert response.status_code == 200
    blobs = _emf_blobs(capsys)
    assert len(blobs) == 1
    blob = blobs[0]
    cw = blob["_aws"]["CloudWatchMetrics"][0]
    assert cw["Namespace"] == settings.POWERTOOLS_METRICS_NAMESPACE
    assert set(cw["Dimensions"][0]) == {"service", "route_template", "status_class"}
    assert {m["Name"] for m in cw["Metrics"]} == {"RequestCount", "Latency"}
    assert blob["service"] == settings.POWERTOOLS_SERVICE_NAME
    assert blob["route_template"] == "/api/health"
    assert blob["status_class"] == "2xx"
    assert blob["RequestCount"] == [1.0]
    assert blob["Latency"][0] >= 0


def test_route_template_dimension_strips_identifier(
    capsys: pytest.CaptureFixture[str],
) -> None:
    phi_like_id = "john-doe-123-45-6789"
    TestClient(app).get(f"/api/providers/{phi_like_id}")

    blobs = _emf_blobs(capsys)
    assert len(blobs) == 1
    assert blobs[0]["route_template"] == "/api/providers/{id}"
    assert blobs[0]["status_class"] == "4xx"
    # No PHI/identifier may survive into ANY dimension value.
    assert phi_like_id not in json.dumps(blobs)


def test_unmatched_route_never_uses_raw_path(
    capsys: pytest.CaptureFixture[str],
) -> None:
    TestClient(app).get("/no-such-route/some-secret-identifier")

    blobs = _emf_blobs(capsys)
    assert len(blobs) == 1
    assert blobs[0]["route_template"] == UNMATCHED_ROUTE
    assert "some-secret-identifier" not in json.dumps(blobs)


def test_error_count_emitted_on_5xx(capsys: pytest.CaptureFixture[str]) -> None:
    client = TestClient(_make_app(), raise_server_exceptions=False)
    response = client.get("/boom")

    assert response.status_code == 500
    blobs = _emf_blobs(capsys)
    assert len(blobs) == 1
    blob = blobs[0]
    assert blob["status_class"] == "5xx"
    assert blob["ErrorCount"] == [1.0]
    metric_names = {m["Name"] for m in blob["_aws"]["CloudWatchMetrics"][0]["Metrics"]}
    assert metric_names == {"RequestCount", "Latency", "ErrorCount"}


def test_error_count_absent_on_success(capsys: pytest.CaptureFixture[str]) -> None:
    TestClient(_make_app()).get("/ok/42")

    blobs = _emf_blobs(capsys)
    assert len(blobs) == 1
    assert "ErrorCount" not in blobs[0]
    assert blobs[0]["route_template"] == "/ok/{id}"


def test_metrics_disabled_emits_nothing(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "METRICS_ENABLED", False)

    TestClient(_make_app()).get("/ok/42")

    assert _emf_blobs(capsys) == []


def test_unhandled_exception_records_500_and_reraises(
    capsys: pytest.CaptureFixture[str],
) -> None:
    client = TestClient(_make_app())
    with pytest.raises(RuntimeError, match="kaboom"):
        client.get("/boom")

    blobs = _emf_blobs(capsys)
    assert len(blobs) == 1
    assert blobs[0]["status_class"] == "5xx"
    assert blobs[0]["ErrorCount"] == [1.0]


def test_sanitize_route_template_normalizes_params() -> None:
    assert (
        sanitize_route_template("/api/providers/{provider_id}/slots")
        == "/api/providers/{id}/slots"
    )
    assert sanitize_route_template("/api/health") == "/api/health"
    assert sanitize_route_template("/{a}/{b}") == "/{id}/{id}"


def test_resolve_route_template_without_matched_route() -> None:
    request = Request({"type": "http", "method": "GET", "path": "/x", "headers": []})
    assert resolve_route_template(request) == UNMATCHED_ROUTE


def test_status_class_buckets() -> None:
    assert status_class(200) == "2xx"
    assert status_class(404) == "4xx"
    assert status_class(500) == "5xx"


def test_cold_start_metric_emitted_once_per_environment(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        main_module, "_mangum_handler", lambda event, context: {"statusCode": 200}
    )
    monkeypatch.setattr(cold_start, "is_cold_start", True)

    main_module.handler({}, None)
    main_module.handler({}, None)

    blobs = _emf_blobs(capsys)
    cold = [b for b in blobs if "ColdStart" in b]
    assert len(cold) == 1
    blob = cold[0]
    assert blob["ColdStart"] == [1.0]
    cw = blob["_aws"]["CloudWatchMetrics"][0]
    assert cw["Namespace"] == settings.POWERTOOLS_METRICS_NAMESPACE
    assert cw["Dimensions"][0] == ["service"]
    assert blob["service"] == settings.POWERTOOLS_SERVICE_NAME


def test_cold_start_metric_skipped_when_warm(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        main_module, "_mangum_handler", lambda event, context: {"statusCode": 200}
    )
    monkeypatch.setattr(cold_start, "is_cold_start", False)

    main_module.handler({}, None)

    assert _emf_blobs(capsys) == []


def test_cold_start_metric_respects_metrics_disabled(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "METRICS_ENABLED", False)
    monkeypatch.setattr(
        main_module, "_mangum_handler", lambda event, context: {"statusCode": 200}
    )
    monkeypatch.setattr(cold_start, "is_cold_start", True)

    main_module.handler({}, None)

    assert _emf_blobs(capsys) == []
