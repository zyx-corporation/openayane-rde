---
title: "RelationStore Schema Specification"
version: "0.1"
date: "2026-05-05"
status: "public-schema-draft"
---

# RelationStore Schema Specification

## 0. Scope

This document specifies the public schema contract for relation-state records used by OpenAyane RDE.

Normative source files:

```text
src/openayane_rde/core/models.py (RelationStoreRecord and related profiles)
```

Current implementation exposes relation-store structure primarily through Pydantic models. A standalone JSON schema file for relation store is planned as a later alignment task.

## 1. Top-level relation record

`RelationStoreRecord` fields:

### 1.1 Required

```text
relation_id: string
subject_id: string
object_id: string
relation_type: enum
trust: number [0.0, 1.0]
stability: number [0.0, 1.0]
context_affinity: number [0.0, 1.0]
interaction_count: integer
critical_corruption_count: integer
suspicious_drift_count: integer
self_report_mismatch_count: integer
self_report_mismatch_item_count: integer
drift_patterns: DriftPattern[]
review_threshold_adjustment: number [0.0, 1.0]
last_delta_m: number
updated_at: date-time
```

### 1.2 Optional

```text
generator_reliability_profile: GeneratorReliabilityProfile | null
document_fragility_profile: DocumentFragilityProfile | null
last_audit_event_id: string | null
```

## 2. Enum sets

### 2.1 relation_type

Current default includes:

```text
generator-document
```

Additional relation types may be introduced with explicit compatibility notes.

### 2.2 DriftPattern.severity

```text
low
medium
high
critical
```

## 3. Nested structures

### 3.1 DriftPattern

```text
pattern_id: string
kind: string (DriftPatternKind enum in models)
count: integer
severity: enum
examples: string[]
last_seen_at: date-time
```

### 3.2 GeneratorReliabilityProfile

```text
generator_id: string
total_outputs: integer
self_report_mismatch_count: integer
critical_corruption_count: integer
suspicious_drift_count: integer
preserved_count: integer
authorized_deviation_count: integer
reliability_score: number [0.0, 1.0]
```

### 3.3 DocumentFragilityProfile

```text
document_id: string
total_edits: integer
protected_change_count: integer
citation_break_count: integer
number_change_count: integer
definition_shift_count: integer
fragility_score: number [0.0, 1.0]
```

## 4. RelationContext (runtime projection)

`RelationContext` is the runtime projection used during evaluation:

```text
subject_id
object_id
trust
stability
context_affinity
interaction_count
last_delta_m
drift_patterns: string[]
drift_pattern_counts: map<string, int>
review_threshold_adjustment
generator_reliability_score?: number
document_fragility_score?: number
last_updated_at?: date-time
```

This projection is not identical to persisted `RelationStoreRecord`, but should be derivable from it.

## 5. Validation and compatibility notes

- Numeric trust-like fields are bounded to `[0.0, 1.0]`.
- RelationStore semantics are operational signals; they are not moral or legal judgement values.
- Any field rename/removal in relation records is a breaking change and must follow `docs/51_openayane_rde_release_compatibility_policy.md`.

## 6. Example

```json
{
  "relation_id": "rel_001",
  "subject_id": "generator:gpt",
  "object_id": "document:phase6-spec",
  "relation_type": "generator-document",
  "trust": 0.62,
  "stability": 0.58,
  "context_affinity": 0.71,
  "interaction_count": 18,
  "critical_corruption_count": 1,
  "suspicious_drift_count": 3,
  "self_report_mismatch_count": 2,
  "self_report_mismatch_item_count": 6,
  "drift_patterns": [
    {
      "pattern_id": "dp_001",
      "kind": "self_report_mismatch",
      "count": 2,
      "severity": "medium",
      "examples": ["numbers changed but reported unchanged"],
      "last_seen_at": "2026-05-05T00:00:00Z"
    }
  ],
  "generator_reliability_profile": null,
  "document_fragility_profile": null,
  "review_threshold_adjustment": 0.15,
  "last_delta_m": 0.44,
  "last_audit_event_id": "audit_20260505_001",
  "updated_at": "2026-05-05T00:00:00Z"
}
```
