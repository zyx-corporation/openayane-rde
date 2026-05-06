# OpenAyane RDE API contract (Phase 5 MVP)

This directory documents the local-only HTTP boundary implemented with Starlette.

## Contract version (M-RDE-G0)

Stable identifier for the `POST /v1/evaluate` envelope (when opt-in is enabled):

- **`contract_version`:** `rde-pre-gateway-integration-v0.2.0` (constant `PRE_GATEWAY_CONTRACT_VERSION` in `app.py`)

## OpenAPI

This MVP does **not** ship an OpenAPI/Swagger document yet. The contract is
documented here and enforced by unit tests.

## Safety posture

- No production authentication guarantee.
- No remote execution surface beyond local Phase 1 evaluation.
- By default, `POST /v1/evaluate` returns `501` and must be explicitly enabled
  by an operator.
- **Pre-gateway baseline:** the service returns **`recommended_action`** (RDE
  `required_action`) and **`policy_action`** (policy bridge) for inspection only.
  **It does not execute** halts, approvals, rollbacks, or any runtime side effect.
  Integrators must apply execution in a separate gateway if needed.

## Migration / 501 behavior table

| Endpoint | Default behaviour (MVP) | When enabled |
|----------|--------------------------|--------------|
| `POST /v1/evaluate` | `501 not_implemented_mvp` | `OPENAYANE_RDE_API_EVALUATE_ENABLED=1` |
| `POST /v1/diff` | `501 not_implemented_mvp` | n/a |
| `POST /v1/execution/evaluate-before` | `501 not_implemented_mvp` | n/a |
| `POST /v1/institution/decide` | `501 not_implemented_mvp` | n/a |
| `GET  /v1/audit/events` | `501 not_implemented_mvp` | n/a |
| `GET  /v1/health` | `200 health` | always |

## Error payload shapes

### 501 (MVP disabled / not implemented)

```json
{
  "error": "not_implemented_mvp",
  "endpoint": "POST /v1/evaluate",
  "note": "Phase 5 skeleton; no production authentication or remote execution."
}
```

### 400 invalid JSON

```json
{
  "error": "invalid_json_body",
  "message": "Request body must be valid JSON."
}
```

### 400 invalid request

```json
{
  "error": "invalid_request",
  "message": [ /* pydantic validation errors */ ]
}
```

## `POST /v1/evaluate` (opt-in enabled)

### Request body

Minimal contract (Phase 1 evaluation):

```json
{
  "task_contract": { /* TaskContract JSON */ },
  "before": "original text",
  "after": "generated text",
  "domain": "markdown" | "json" | "python" | "generic",
  "required_json_fields": ["name", "version", "status"], 
  "self_report": { /* SelfReport JSON (optional) */ }
}
```

Notes:

- `domain="generic"` behaves like `domain="markdown"` for this MVP.
- If `required_json_fields` is provided for `domain="json"`, it is passed into the JSON structural diff.

### Response body (200, opt-in enabled)

The **`rde_result`** object is a JSON serialization of `RDEResult` and **MUST**
validate against [`schemas/rde_result.schema.json`](../../schemas/rde_result.schema.json)
(`rde_result_schema` URI is repeated in the payload for gateway discovery).

```json
{
  "contract_version": "rde-pre-gateway-integration-v0.2.0",
  "rde_result_schema": "https://github.com/zyx-corporation/openayane-rde/schemas/rde_result.schema.json",
  "rde_result": { },
  "recommended_action": "approve",
  "classification": "preserved",
  "risk_level": "low",
  "policy_action": "approve",
  "rde_result_id": "rde_xxx",
  "policy_decision_id": "pd_xxx",
  "audit_event_id": null,
  "task_contract_id": "tc_xxx"
}
```

- **`recommended_action`:** same value as `rde_result.required_action` (RDE
  recommendation). **Not executed** by this HTTP service.
- **`policy_action`:** result of `decide_policy` for the same run. **Not executed**
  by this HTTP service.
- Summary fields (`classification`, `risk_level`, …) duplicate `rde_result` /
  policy ids for backward compatibility and shallow clients.

## Test linkage

Contract tests are located in:

- `tests/unit/test_api_health.py`

