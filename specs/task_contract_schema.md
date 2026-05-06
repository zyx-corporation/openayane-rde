---
title: "TaskContract — Schema specification"
version: "0.1"
status: "draft"
date: "2026-05-06"
---

# TaskContract — Schema specification

## Canonical definition

- **JSON Schema:** [`../schemas/task_contract.schema.json`](../schemas/task_contract.schema.json)
- **Pydantic model:** `TaskContract` in `openayane_rde.core.models`

Serialized JSON instances MUST validate against the JSON Schema. The schema ID is embedded in the file (`$id`).

## Required fields

| Field | Meaning |
|-------|---------|
| `contract_id` | Unique identifier for this contract. |
| `mode` | One of: `preservation`, `creative`, `refactor`, `research`, `execution`. |
| `target_scope` | Object with `files`, `symbols`, `sections` (arrays of strings). |
| `requested_action` | Human-readable description of the requested transformation. |
| `allowed_delta_m` | List of allowed meaning-change descriptions (string phrases). |
| `forbidden_delta_m` | List of forbidden change descriptions. |
| `protected_elements` | List of `ProtectedElementKind` enum strings (see schema enum). |
| `output_policy` | `require_patch`, `require_change_report`, `require_uncertainty_report` (booleans). |
| `review_policy` | Per-classification default review actions (see below). |
| `created_at` | ISO 8601 date-time string. |

## Optional fields

| Field | Meaning |
|-------|---------|
| `relation_context_ref` | Reference into relation / history context (nullable string). |
| `metadata` | Open object for integrator-specific metadata. |

## `review_policy` structure

Required nested keys (each maps to a controlled string enum per JSON Schema):

| Key | Typical intent |
|-----|----------------|
| `preserved` | `auto_approve` \| `approve_with_note` \| `human_review` |
| `authorized_deviation` | same enum as preserved |
| `benign_incidental_drift` | `approve_with_note` \| `human_review` |
| `suspicious_drift` | `human_review` \| `request_revision` |
| `critical_corruption` | `halt` \| `rollback` |

## Example (minimal)

```json
{
  "contract_id": "tc_example",
  "mode": "preservation",
  "target_scope": { "files": ["doc.md"], "symbols": [], "sections": [] },
  "requested_action": "Fix typos only",
  "allowed_delta_m": ["typo correction"],
  "forbidden_delta_m": ["change factual claims"],
  "protected_elements": ["claims", "citations"],
  "output_policy": {
    "require_patch": true,
    "require_change_report": true,
    "require_uncertainty_report": false
  },
  "review_policy": {
    "preserved": "auto_approve",
    "authorized_deviation": "approve_with_note",
    "benign_incidental_drift": "approve_with_note",
    "suspicious_drift": "human_review",
    "critical_corruption": "halt"
  },
  "created_at": "2026-05-06T12:00:00Z"
}
```

## Compatibility

Breaking changes to required fields, enums, or semantics are governed by **`docs/51_openayane_rde_release_compatibility_policy.md`**. Schema and model updates should stay in sync; CI validates fixtures against `schemas/` when using `openayane-rde schema validate`.
