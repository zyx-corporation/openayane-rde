---
title: "Relation store — Schema specification"
version: "0.1"
status: "draft"
date: "2026-05-06"
---

# Relation store — Schema specification

## Status

There is **no** top-level `schemas/relation_store.schema.json` in this repository yet. The canonical serialized shape for Phase 2 relation persistence is defined by **Pydantic models** and the JSON-backed store implementation.

**Primary references:**

- `RelationStoreRecord`, `RelationContext`, `DriftPattern`, `GeneratorReliabilityProfile`, `DocumentFragilityProfile`, `RelationUpdateSummary` in `openayane_rde.core.models`
- Runtime persistence: `JSONRelationStore` (Phase 2 minimal; single-file JSON, not concurrent-production-grade — see `README.md`)

When a formal JSON Schema is added under `schemas/`, this document should be updated to reference it and duplicate required/optional lists should be removed in favour of the schema file.

## RelationStoreRecord (conceptual)

| Field | Required | Meaning |
|-------|----------|---------|
| `relation_id` | yes | Unique relation row id. |
| `subject_id` | yes | Subject entity id. |
| `object_id` | yes | Object entity id. |
| `relation_type` | default | `generator-document` \| `agent-document` \| `user-agent` \| `tool-workspace` \| `domain-policy`. |
| `trust`, `stability`, `context_affinity` | yes | Floats in [0, 1]. |
| `interaction_count` | yes | Integer counter. |
| `critical_corruption_count`, `suspicious_drift_count` | yes | Drift tallies. |
| `self_report_mismatch_count`, `self_report_mismatch_item_count` | yes | Self-report inconsistency metrics. |
| `drift_patterns` | yes | List of `DriftPattern` objects. |
| `generator_reliability_profile` | no | Optional aggregate generator stats. |
| `document_fragility_profile` | no | Optional per-document fragility stats. |
| `review_threshold_adjustment` | yes | Threshold tuning in [0, 1]. |
| `last_delta_m` | yes | Last observed ΔM scalar used by relation logic. |
| `last_audit_event_id` | no | Optional link to last audit event. |
| `updated_at` | yes | ISO 8601 timestamp. |

## DriftPattern

| Field | Meaning |
|-------|---------|
| `pattern_id` | Unique id. |
| `kind` | `DriftPatternKind` string (e.g. `citation_deletion`, `self_report_mismatch`, …). |
| `count` | Occurrence count. |
| `severity` | `low` \| `medium` \| `high` \| `critical`. |
| `examples` | Optional string examples. |
| `last_seen_at` | Timestamp. |

## RelationUpdateSummary

Outcome object when applying evaluation results to relation state (Phase 2 hook): carries `RelationContext`, optional before/after trust and threshold fields, `updated_patterns`, and a human `message`.

## Compatibility

Relation record shape changes affect historical JSON stores and tests. Treat additions of optional fields as non-breaking when documented; renaming or removing fields requires a migration note under **`docs/51_openayane_rde_release_compatibility_policy.md`** for operator-facing persistence.

## Example (RelationStoreRecord sketch)

```json
{
  "relation_id": "rel_example",
  "subject_id": "gen_1",
  "object_id": "doc_42",
  "relation_type": "generator-document",
  "trust": 0.55,
  "stability": 0.6,
  "context_affinity": 0.5,
  "interaction_count": 12,
  "critical_corruption_count": 0,
  "suspicious_drift_count": 2,
  "self_report_mismatch_count": 1,
  "self_report_mismatch_item_count": 3,
  "drift_patterns": [],
  "generator_reliability_profile": null,
  "document_fragility_profile": null,
  "review_threshold_adjustment": 0.1,
  "last_delta_m": 0.35,
  "last_audit_event_id": "ae_example",
  "updated_at": "2026-05-06T12:05:00Z"
}
```
