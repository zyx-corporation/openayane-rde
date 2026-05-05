---
title: "RDEResult Schema Specification"
version: "0.1"
date: "2026-05-05"
status: "public-schema-draft"
---

# RDEResult Schema Specification

## 0. Scope

This document specifies the public schema contract for `RDEResult`.

Normative source files:

```text
src/openayane_rde/core/models.py (RDEResult and nested types)
schemas/rde_result.schema.json
```

## 1. Required and optional fields

### 1.1 Required

```text
result_id: string
contract_id: string
classification: enum
resonance_score: number [0.0, 1.0]
preservation_score: number [0.0, 1.0]
authorization_score: number [0.0, 1.0]
risk_level: enum
violated_constraints: ConstraintViolation[]
suspicious_elements: SuspiciousElement[]
required_action: enum
explanation: string
created_at: date-time
```

### 1.2 Optional

```text
score_details: object | null
metadata: object
evaluation_kind: enum | null
evidence_basis: enum[]
```

## 2. Enum sets

### 2.1 classification

```text
preserved
authorized_deviation
benign_incidental_drift
suspicious_drift
critical_corruption
creative_deviation
```

### 2.2 risk_level

```text
low
medium
high
critical
```

### 2.3 required_action

```text
approve
approve_with_notes
request_revision
human_review
halt
rollback
```

### 2.4 evaluation_kind

```text
pre_synthetic
post_structural
null
```

### 2.5 evidence_basis

```text
tool_risk_rule
execution_contract
structural_diff
semantic_delta
observed_side_effects
rollback_result
human_review_decision
llm_assisted_semantic_evaluation
```

## 3. Nested objects

### 3.1 ConstraintViolation

```text
constraint: string (required)
path: string | null (optional)
description: string (required)
severity: low | medium | high | critical (required)
```

### 3.2 SuspiciousElement

```text
element: string (required)
path: string (required)
description: string (required)
risk_hint: low | medium | high | critical | unknown (required)
```

### 3.3 score_details

Known keys:

```text
structural_risk_score
semantic_delta_score
self_report_mismatch_score
relation_adjustment_score
```

`score_details` allows additional properties for forward-compatible scoring metadata.

## 4. Validation and compatibility notes

- Top-level `additionalProperties` is forbidden.
- Consumers should not assume `evaluation_kind` and `evidence_basis` are always present for legacy records.
- Breaking changes must follow `docs/51_openayane_rde_release_compatibility_policy.md`.

## 5. Example

```json
{
  "result_id": "rde_001",
  "contract_id": "tc_001",
  "classification": "suspicious_drift",
  "resonance_score": 0.32,
  "preservation_score": 0.41,
  "authorization_score": 0.25,
  "risk_level": "high",
  "violated_constraints": [
    {
      "constraint": "protected numbers must remain unchanged",
      "path": "section:metrics",
      "description": "Critical metric value changed from 10 to 100",
      "severity": "high"
    }
  ],
  "suspicious_elements": [
    {
      "element": "numbers",
      "path": "section:metrics",
      "description": "Unexpected magnitude change",
      "risk_hint": "high"
    }
  ],
  "required_action": "human_review",
  "explanation": "Protected numerical claim changed outside allowed delta.",
  "score_details": {
    "structural_risk_score": 0.8,
    "semantic_delta_score": 0.6,
    "self_report_mismatch_score": 0.5,
    "relation_adjustment_score": 0.2
  },
  "metadata": {},
  "evaluation_kind": "post_structural",
  "evidence_basis": ["structural_diff", "semantic_delta"],
  "created_at": "2026-05-05T00:00:00Z"
}
```
