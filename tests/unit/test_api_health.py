"""Local API skeleton smoke tests (#46)."""

from __future__ import annotations

from starlette.testclient import TestClient

from openayane_rde.api.app import build_app


def test_health_ok() -> None:
    client = TestClient(build_app())
    r = client.get("/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["authentication"] == "none"


def test_evaluate_is_not_implemented() -> None:
    client = TestClient(build_app())
    r = client.post("/v1/evaluate", json={})
    assert r.status_code == 501
