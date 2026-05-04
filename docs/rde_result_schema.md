# RDEResult JSON Schema Specification

## 1. Purpose

`RDEResult` is the output of the RDE Core.

RDE is an evaluator. It evaluates semantic change ΔM and classifies whether the change is preserved, authorized, suspicious, corruptive, or creative.

`RDEResult` does not directly apply changes. It provides evidence and recommendation to the OpenAyane mechanism, especially the Policy Bridge and Modification Control Flow.

```text
RDE Core
  ↓
RDEResult
  ↓
Policy Bridge
  ↓
PolicyDecision
  ↓
Modification Control Flow
```

## 2. Design Principles

### 2.1 RDE evaluates; OpenAyane acts

`RDEResult.required_action` is a recommendation, not the final execution decision.

### 2.2 Classification and risk are separate

A classification describes the type of semantic deviation. `risk_level` describes operational risk.

For example:

```text
creative_deviation + low risk:
  acceptable in creative mode

creative_deviation + high risk:
  human review required

benign_incidental_drift + critical domain:
  human review may still be required
```

### 2.3 Explanation is required

Every RDE result must include an explanation sufficient for audit and human review.

## 3. JSON Schema Draft

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/zyx-corporation/openayane-rde/schemas/rde_result.schema.json",
  "title": "RDEResult",
  "type": "object",
  "required": [
    "result_id",
    "contract_id",
    "classification",
    "resonance_score",
    "preservation_score",
    "authorization_score",
    "risk_level",
    "violated_constraints",
    "suspicious_elements",
    "required_action",
    "explanation",
    "created_at"
  ],
  "properties": {
    "result_id": { "type": "string" },
    "contract_id": { "type": "string" },
    "classification": {
      "type": "string",
      "enum": [
        "preserved",
        "authorized_deviation",
        "benign_incidental_drift",
        "suspicious_drift",
        "critical_corruption",
        "creative_deviation"
      ]
    },
    "resonance_score": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0
    },
    "preservation_score": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0
    },
    "authorization_score": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0
    },
    "risk_level": {
      "type": "string",
      "enum": ["low", "medium", "high", "critical"]
    },
    "violated_constraints": {
      "type": "array",
      "items": { "$ref": "#/$defs/constraint_violation" }
    },
    "suspicious_elements": {
      "type": "array",
      "items": { "$ref": "#/$defs/suspicious_element" }
    },
    "required_action": {
      "type": "string",
      "enum": [
        "approve",
        "approve_with_notes",
        "request_revision",
        "human_review",
        "halt",
        "rollback"
      ]
    },
    "explanation": {
      "type": "string"
    },
    "score_details": {
      "type": "object",
      "properties": {
        "structural_risk_score": { "type": "number" },
        "semantic_delta_score": { "type": "number" },
        "self_report_mismatch_score": { "type": "number" },
        "relation_adjustment_score": { "type": "number" }
      },
      "additionalProperties": true
    },
    "metadata": {
      "type": "object",
      "additionalProperties": true
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "$defs": {
    "constraint_violation": {
      "type": "object",
      "required": ["constraint", "description", "severity"],
      "properties": {
        "constraint": { "type": "string" },
        "path": { "type": ["string", "null"] },
        "description": { "type": "string" },
        "severity": {
          "type": "string",
          "enum": ["low", "medium", "high", "critical"]
        }
      },
      "additionalProperties": false
    },
    "suspicious_element": {
      "type": "object",
      "required": ["element", "path", "description", "risk_hint"],
      "properties": {
        "element": { "type": "string" },
        "path": { "type": "string" },
        "description": { "type": "string" },
        "risk_hint": {
          "type": "string",
          "enum": ["low", "medium", "high", "critical", "unknown"]
        }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

## 4. Classification Semantics

### 4.1 preserved

Meaning and protected elements are preserved.

Surface or structural changes may exist, but they do not alter protected meaning.

### 4.2 authorized_deviation

Meaning changed, but the change is explicitly allowed by the TaskContract.

### 4.3 benign_incidental_drift

Minor drift exists outside the requested scope, but it does not materially affect protected claims, constraints, references, execution semantics, or safety conditions.

In high-stakes domains, this classification should be used conservatively.

### 4.4 suspicious_drift

Unrequested semantic or structural change exists, and its acceptability is unclear.

Requires human review or revision request.

### 4.5 critical_corruption

A protected or safety-critical element was damaged.

Examples:

```text
- number changed
- citation removed
- definition weakened
- function signature changed
- required JSON field deleted
- safety condition removed
- credential exposed
```

### 4.6 creative_deviation

The output intentionally departs from the original structure or claim space.

Creative deviation is not automatically bad, but it must be signed, explainable, reversible when required, and bounded by protected elements.

## 5. Example

```json
{
  "result_id": "rde_001",
  "contract_id": "tc_001",
  "classification": "suspicious_drift",
  "resonance_score": 0.42,
  "preservation_score": 0.68,
  "authorization_score": 0.31,
  "risk_level": "high",
  "violated_constraints": [
    {
      "constraint": "claims must not change",
      "path": "/sections/2/paragraphs/3",
      "description": "Protected claim changed from RDE is not Policy to RDE may be Policy.",
      "severity": "high"
    }
  ],
  "suspicious_elements": [
    {
      "element": "claims",
      "path": "/sections/2/paragraphs/3",
      "description": "Core definition boundary changed.",
      "risk_hint": "high"
    }
  ],
  "required_action": "human_review",
  "explanation": "The generated output changed a protected claim and the change was not listed in allowed_delta_m. Generator self_report claimed that claims were unchanged.",
  "score_details": {
    "structural_risk_score": 0.74,
    "semantic_delta_score": 0.62,
    "self_report_mismatch_score": 0.88,
    "relation_adjustment_score": 0.10
  },
  "metadata": {},
  "created_at": "2026-05-04T00:00:00Z"
}
```

## 6. Phase 1 Notes

Phase 1 RDE Core may be rule-based.

Minimum required classifications:

```text
preserved
authorized_deviation
suspicious_drift
critical_corruption
```

Optional in Phase 1:

```text
benign_incidental_drift
creative_deviation
```

Phase 1 RDE should prioritize recall for `critical_corruption` over reducing false positives.
