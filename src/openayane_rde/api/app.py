"""Starlette app: health + explicit 501 stubs (no remote execution surface)."""

from __future__ import annotations

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route


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
    return Starlette(
        routes=[
            Route("/v1/health", health, methods=["GET"]),
            Route("/v1/evaluate", stub_evaluate, methods=["POST"]),
            Route("/v1/diff", stub_diff, methods=["POST"]),
            Route("/v1/execution/evaluate-before", stub_execution_evaluate_before, methods=["POST"]),
            Route("/v1/institution/decide", stub_institution_decide, methods=["POST"]),
            Route("/v1/audit/events", stub_audit_events, methods=["GET"]),
        ],
    )
