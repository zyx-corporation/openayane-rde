---
title: "AuditEvent — Schema specification"
version: "0.1"
status: "draft"
date: "2026-05-06"
---

# AuditEvent — Schema specification

## Canonical definition

- **JSON Schema:** [`../schemas/audit_event.schema.json`](../schemas/audit_event.schema.json)
- **Pydantic model:** `AuditEvent` in `openayane_rde.core.models`

Audit events are append-only records suitable for operator pipelines and CI regression locks.

## Required fields

| Field | Meaning |
|-------|---------|
| `event_id` | Unique event identifier. |
| `timestamp` | ISO 8601 date-time. |
| `actor` | One of: `user`, `agent`, `generator`, `rde`, `policy`, `runtime`, `reviewer`, `system`. |
| `action` | Audit verb — see large enum in JSON Schema (contract creation, diff, RDE, execution gate, rollback, etc.). |
| `explanation` | Human-readable description of the event. |

## Optional correlation IDs

All nullable strings linking to other artefacts:

`task_contract_id`, `generator_output_id`, `structural_diff_id`, `semantic_delta_id`, `rde_result_id`, `policy_decision_id`, `execution_result_id`

## Integrity fields

| Field | Meaning |
|-------|---------|
| `hash_before` | Optional `sha256:` + 64 hex chars (content hash before change). |
| `hash_after` | Optional `sha256:` + 64 hex chars (content hash after change). |

## Payload and errors

| Field | Meaning |
|-------|---------|
| `payload` | JSON object — additional structured context (schema allows additional properties in model usage; JSON Schema may constrain — follow repo schema file). |
| `error` | Optional structured error (`error_type`, `message`, `recoverable`). |

**Note:** The published JSON Schema sets `additionalProperties: false` at the root; extended audit payloads must fit allowed fields or the schema must be versioned per compatibility policy.

## Example (minimal)

```json
{
  "event_id": "ae_example",
  "timestamp": "2026-05-06T12:00:02Z",
  "actor": "rde",
  "task_contract_id": "tc_example",
  "generator_output_id": null,
  "structural_diff_id": "sdiff_example",
  "semantic_delta_id": null,
  "rde_result_id": "rde_example",
  "policy_decision_id": null,
  "execution_result_id": null,
  "action": "evaluate_rde",
  "hash_before": null,
  "hash_after": null,
  "explanation": "RDE evaluation completed.",
  "payload": {},
  "error": null
}
```

## Compatibility

Renaming or removing `action` literals consumed by tooling is **breaking** per **`docs/51_openayane_rde_release_compatibility_policy.md`**. New actions may be added as non-breaking when documented.
