"""Local API skeleton smoke tests (#46)."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
from starlette.testclient import TestClient

from openayane_rde.api.app import PRE_GATEWAY_CONTRACT_VERSION, build_app
from openayane_rde.contract.builder import build_contract

_SCHEMAS = Path(__file__).resolve().parent.parent.parent / "schemas"


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
    body = r.json()
    assert body["error"] == "not_implemented_mvp"
    assert body["endpoint"] == "POST /v1/evaluate"
    assert "Phase 5 skeleton" in body["note"]


def test_evaluate_enabled_runs() -> None:
    import os

    os.environ["OPENAYANE_RDE_API_EVALUATE_ENABLED"] = "1"
    try:
        contract = build_contract(
            mode="preservation",
            requested_action="Preserve content.",
            protected_elements=["citations", "numbers"],
        )
        before = "Some content with [ref](https://example.com) and value 42."
        req = {
            "task_contract": json.loads(contract.model_dump_json()),
            "before": before,
            "after": before,
            "domain": "markdown",
        }
        client = TestClient(build_app())
        r = client.post("/v1/evaluate", json=req)
        assert r.status_code == 200
        body = r.json()
        assert body["contract_version"] == PRE_GATEWAY_CONTRACT_VERSION
        assert body["rde_result_schema"].endswith("/schemas/rde_result.schema.json")
        assert body["classification"] == "preserved"
        assert body["policy_action"] == "approve"
        assert body["recommended_action"] == "approve"
        assert body["recommended_action"] == body["rde_result"]["required_action"]
        schema = json.loads((_SCHEMAS / "rde_result.schema.json").read_text())
        jsonschema.validate(body["rde_result"], schema)
    finally:
        os.environ.pop("OPENAYANE_RDE_API_EVALUATE_ENABLED", None)


def test_evaluate_enabled_invalid_json_returns_400() -> None:
    import os

    os.environ["OPENAYANE_RDE_API_EVALUATE_ENABLED"] = "1"
    try:
        client = TestClient(build_app())
        r = client.post(
            "/v1/evaluate",
            content=b"{not-json",
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == 400
        body = r.json()
        assert body["error"] == "invalid_json_body"
    finally:
        os.environ.pop("OPENAYANE_RDE_API_EVALUATE_ENABLED", None)


def test_evaluate_enabled_invalid_request_returns_400() -> None:
    import os

    os.environ["OPENAYANE_RDE_API_EVALUATE_ENABLED"] = "1"
    try:
        client = TestClient(build_app())
        r = client.post("/v1/evaluate", json={})
        assert r.status_code == 400
        body = r.json()
        assert body["error"] == "invalid_request"
        assert isinstance(body["message"], list)
    finally:
        os.environ.pop("OPENAYANE_RDE_API_EVALUATE_ENABLED", None)
