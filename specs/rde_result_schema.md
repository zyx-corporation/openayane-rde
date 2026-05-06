---
title: "RDEResult — Schema specification"
version: "0.1"
status: "draft"
date: "2026-05-06"
---

# RDEResult — Schema specification

## Canonical definition

- **JSON Schema:** [`../schemas/rde_result.schema.json`](../schemas/rde_result.schema.json)
- **Pydantic model:** `RDEResult` in `openayane_rde.core.models`

## Required fields

| Field | Meaning |
|-------|---------|
| `result_id` | Unique identifier for this evaluation result. |
| `contract_id` | Links to the `TaskContract` evaluated. |
| `classification` | `RDEClassification` — see enum in JSON Schema. |
| `resonance_score` | Score in [0, 1]. |
| `preservation_score` | Score in [0, 1]. |
| `authorization_score` | Score in [0, 1]. |
| `risk_level` | `low` \| `medium` \| `high` \| `critical`. |
| `violated_constraints` | Array of constraint violation objects. |
| `suspicious_elements` | Array of suspicious element objects. |
| `required_action` | Advisory action: `approve`, `approve_with_notes`, `request_revision`, `human_review`, `halt`, `rollback`. |
| `explanation` | Human-readable rationale. |
| `created_at` | ISO 8601 date-time. |

## Optional fields

| Field | Meaning |
|-------|---------|
| `score_details` | Optional breakdown (`structural_risk_score`, `semantic_delta_score`, etc.). |
| `metadata` | Open object. |
| `evaluation_kind` | `pre_synthetic` \| `post_structural` or null. |
| `evidence_basis` | Array of evidence source strings (see schema enum). |

## Classification enum

Must be one of:

`preserved`, `authorized_deviation`, `benign_incidental_drift`, `suspicious_drift`, `critical_corruption`, `creative_deviation`.

See **`specs/rde_core_spec.md`** for semantic reading of each value.

## Example (minimal)

```json
{
  "result_id": "rde_example",
  "contract_id": "tc_example",
  "classification": "suspicious_drift",
  "resonance_score": 0.4,
  "preservation_score": 0.7,
  "authorization_score": 0.3,
  "risk_level": "high",
  "violated_constraints": [],
  "suspicious_elements": [
    {
      "element": "citations",
      "path": "/section[2]",
      "description": "Citation removed",
      "risk_hint": "high"
    }
  ],
  "required_action": "human_review",
  "explanation": "Protected citation element changed.",
  "created_at": "2026-05-06T12:00:01Z"
}
```

## Compatibility

Breaking changes are governed by **`docs/51_openayane_rde_release_compatibility_policy.md`**. Altering classification semantics for the same inputs is treated as a **breaking** operator-visible change unless documented as a deliberate bugfix with RDE review.
