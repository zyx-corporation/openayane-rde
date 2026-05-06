---
title: "Relation store — Schema specification"
version: "0.2"
status: "draft"
date: "2026-05-06"
---

# Relation store — Schema specification

## Status

The canonical top-level JSON Schema for serialized `RelationStoreRecord` objects is now:

```text
schemas/relation_store.schema.json
```

The schema is aligned with `RelationStoreRecord` and related Pydantic models in `openayane_rde.core.models`, and is covered by schema/model synchronization and jsonschema validation tests.

**Primary references:**

- Canonical JSON Schema: `schemas/relation_store.schema.json`
- Pydantic models: `RelationStoreRecord`, `RelationContext`, `DriftPattern`, `GeneratorReliabilityProfile`, `DocumentFragilityProfile`, `RelationUpdateSummary` in `openayane_rde.core.models`
- Runtime persistence: `JSONRelationStore` (Phase 2 minimal; single-file JSON, not concurrent-production-grade — see `README.md`)

## Validation boundary

`schemas/relation_store.schema.json` validates the serialized **structure** of a relation-store record:

- required fields
- enum domains such as `relation_type` and drift pattern kind
- numeric score ranges for `trust`, `stability`, `context_affinity`, profile scores, and threshold adjustment
- nested profile object shape
- rejection of unexpected top-level and nested fields

It does **not** validate the semantic correctness of a relation update. In particular, JSON Schema does not prove that trust, stability, context affinity, drift patterns, or review-threshold adjustments were updated from sufficient audit evidence or by the intended RDE logic. Those constraints remain governed by implementation tests, audit discipline, and `specs/known_limitations.md`.

## RelationStoreRecord

The required and optional field lists are defined by `schemas/relation_store.schema.json`. The conceptual meaning is summarized here for readability.

| Field | Meaning |
|-------|---------|
| `relation_id` | Unique relation row id. |
| `subject_id` | Subject entity id. |
| `object_id` | Object entity id. |
| `relation_type` | `generator-document` \| `agent-document` \| `user-agent` \| `tool-workspace` \| `domain-policy`. |
| `trust`, `stability`, `context_affinity` | Floats in [0, 1]. |
| `interaction_count` | Integer counter. |
| `critical_corruption_count`, `suspicious_drift_count` | Drift tallies. |
| `self_report_mismatch_count`, `self_report_mismatch_item_count` | Self-report inconsistency metrics. |
| `drift_patterns` | List of `DriftPattern` objects. |
| `generator_reliability_profile` | Optional aggregate generator stats. |
| `document_fragility_profile` | Optional per-document fragility stats. |
| `review_threshold_adjustment` | Threshold tuning in [0, 1]. |
| `last_delta_m` | Last observed ΔM scalar used by relation logic. |
| `last_audit_event_id` | Optional link to last audit event. |
| `updated_at` | ISO 8601 timestamp. |

## DriftPattern

| Field | Meaning |
|-------|---------|
| `pattern_id` | Unique id. |
| `kind` | `DriftPatternKind` string, e.g. `citation_deletion`, `self_report_mismatch`. |
| `count` | Occurrence count. |
| `severity` | `low` \| `medium` \| `high` \| `critical`. |
| `examples` | String examples. |
| `last_seen_at` | Timestamp. |

## RelationUpdateSummary

`RelationUpdateSummary` is an outcome object when applying evaluation results to relation state. It carries `RelationContext`, optional before/after trust and threshold fields, `updated_patterns`, and a human-readable `message`.

It is intentionally not the top-level persisted relation record and is not covered by `schemas/relation_store.schema.json`.

## Compatibility

Relation record shape changes affect historical JSON stores and tests. Treat additions of optional fields as non-breaking when documented; renaming or removing fields requires a migration note under **`docs/51_openayane_rde_release_compatibility_policy.md`** for operator-facing persistence.

Schema changes must preserve the distinction between structural validation and RDE semantic validation. Expanding the schema must not be described as lifting limitations on semantic equivalence, field performance, or production identity.

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
