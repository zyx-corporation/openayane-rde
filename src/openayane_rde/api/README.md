# OpenAyane RDE API contract (Phase 5 MVP)

This directory documents the local-only HTTP boundary implemented with Starlette.

## OpenAPI

This MVP does **not** ship an OpenAPI/Swagger document yet. The contract is
documented here and enforced by unit tests.

## Safety posture

- No production authentication guarantee.
- No remote execution surface beyond local Phase 1 evaluation.
- By default, `POST /v1/evaluate` returns `501` and must be explicitly enabled
  by an operator.

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

### Response body

```json
{
  "classification": "preserved" ,
  "risk_level": "low",
  "policy_action": "approve",
  "rde_result_id": "rde_xxx",
  "policy_decision_id": "pd_xxx",
  "audit_event_id": null,
  "task_contract_id": "tc_xxx"
}
```

## Test linkage

Contract tests are located in:

- `tests/unit/test_api_health.py`

