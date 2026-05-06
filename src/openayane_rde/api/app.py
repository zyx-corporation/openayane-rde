"""Starlette app: health + local-only API surface.

Phase 5 intentionally keeps remote execution surfaces out of default operation.
The evaluation endpoint is enabled only when an operator explicitly opts in
via environment variables.
"""

from __future__ import annotations

import os
from typing import Any, Literal, cast

from pydantic import BaseModel, ValidationError
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from openayane_rde.core.models import GeneratorOutput, ModelInfo, SelfReport, TaskContract
from openayane_rde.runtime._flow import run_phase1_evaluation


_API_EVALUATE_ENABLED_ENV = "OPENAYANE_RDE_API_EVALUATE_ENABLED"

# M-RDE-G0: pre-gateway integration baseline (see CHANGELOG [0.2.0]).
PRE_GATEWAY_CONTRACT_VERSION = "rde-pre-gateway-integration-v0.2.0"
RDE_RESULT_SCHEMA_URI = (
    "https://github.com/zyx-corporation/openayane-rde/schemas/rde_result.schema.json"
)


def _api_evaluate_enabled() -> bool:
    raw = os.getenv(_API_EVALUATE_ENABLED_ENV, "")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


Domain = Literal["markdown", "json", "python", "generic"]
RunDomain = Literal["markdown", "json", "python"]


class EvaluateRequest(BaseModel):
    task_contract: TaskContract
    before: str
    after: str
    domain: Domain = "markdown"
    required_json_fields: list[str] | None = None
    self_report: SelfReport | None = None
    model_config = {"extra": "forbid"}


async def health(_: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "service": "openayane-rde",
            "authentication": "none",
            "scope": "local_development_only",
        }
    )


async def _stub(name: str) -> JSONResponse:
    return JSONResponse(
        {
            "error": "not_implemented_mvp",
            "endpoint": name,
            "note": "Phase 5 skeleton; no production authentication or remote execution.",
        },
        status_code=501,
    )


async def stub_evaluate(_: Request) -> JSONResponse:
    return await _stub("POST /v1/evaluate")


async def stub_diff(_: Request) -> JSONResponse:
    return await _stub("POST /v1/diff")


async def stub_execution_evaluate_before(_: Request) -> JSONResponse:
    return await _stub("POST /v1/execution/evaluate-before")


async def stub_institution_decide(_: Request) -> JSONResponse:
    return await _stub("POST /v1/institution/decide")


async def stub_audit_events(_: Request) -> JSONResponse:
    return await _stub("GET /v1/audit/events")


def build_app() -> Starlette:
    # The routes are fixed, but the handler may return 501 unless enabled.
    return Starlette(
        routes=[
            Route("/v1/health", health, methods=["GET"]),
            Route("/v1/evaluate", evaluate, methods=["POST"]),
            Route("/v1/diff", stub_diff, methods=["POST"]),
            Route("/v1/execution/evaluate-before", stub_execution_evaluate_before, methods=["POST"]),
            Route("/v1/institution/decide", stub_institution_decide, methods=["POST"]),
            Route("/v1/audit/events", stub_audit_events, methods=["GET"]),
        ],
    )


async def evaluate(request: Request) -> JSONResponse:
    """Run Phase 1 evaluation for local inspection (opt-in via env var)."""
    if not _api_evaluate_enabled():
        return await stub_evaluate(request)

    try:
        payload: dict[str, Any] = cast(dict[str, Any], await request.json())
    except Exception:
        return JSONResponse(
            {"error": "invalid_json_body", "message": "Request body must be valid JSON."},
            status_code=400,
        )

    try:
        req = EvaluateRequest.model_validate(payload)
    except ValidationError as exc:
        return JSONResponse(
            {"error": "invalid_request", "message": exc.errors()},
            status_code=400,
        )

    domain: RunDomain = "markdown" if req.domain == "generic" else req.domain

    go = GeneratorOutput(
        contract_id=req.task_contract.contract_id,
        output_type="full_text",
        payload=req.after,
        self_report=req.self_report or SelfReport(),
        model_info=ModelInfo(provider="local", model="openayane-rde-api"),
    )

    result = run_phase1_evaluation(
        original=req.before,
        generator_output=go,
        task_contract=req.task_contract,
        domain=domain,
        required_json_fields=req.required_json_fields,
    )

    rde_json = result.rde_result.model_dump(mode="json")
    out = {
        "contract_version": PRE_GATEWAY_CONTRACT_VERSION,
        "rde_result_schema": RDE_RESULT_SCHEMA_URI,
        "rde_result": rde_json,
        "recommended_action": result.rde_result.required_action,
        "classification": result.rde_result.classification,
        "risk_level": result.rde_result.risk_level,
        "policy_action": result.policy_decision.action,
        "rde_result_id": result.rde_result.result_id,
        "policy_decision_id": result.policy_decision.decision_id,
        "audit_event_id": result.audit_event.event_id if result.audit_event else None,
        "task_contract_id": result.task_contract.contract_id,
    }
    return JSONResponse(out, status_code=200)
