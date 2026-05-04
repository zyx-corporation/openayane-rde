# AuditEvent JSON Schema Specification

## 1. Purpose

`AuditEvent` records what happened in the OpenAyane mechanism.

AuditLog is not an optional debug log. It is the institutional memory of OpenAyane.

It records:

- which TaskContract was used,
- what GeneratorOutput was produced,
- what StructuralDiff was detected,
- what SemanticDelta was estimated,
- what RDEResult was returned,
- what PolicyDecision was made,
- what ExecutionResult occurred,
- who or what acted,
- what changed before and after,
- why the decision was made.

AuditEvent is also the primary source for RelationStore updates.

```text
AuditEvent
  ↓
RelationStore Update
  ↓
Historical Feedback Loop
```

## 2. Design Principles

### 2.1 Audit before relation update

RelationStore must not update trust or stability without auditable evidence.

### 2.2 Hash before and after

When a state change is proposed or applied, OpenAyane should store `hash_before` and `hash_after`.

### 2.3 Human review must be recorded

Human review outcomes are part of the institutional feedback loop.

### 2.4 AuditLog is append-only in principle

Phase 1 may use JSONL, but the conceptual model is append-only.

## 3. JSON Schema Draft

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/zyx-corporation/openayane-rde/schemas/audit_event.schema.json",
  "title": "AuditEvent",
  "type": "object",
  "required": [
    "event_id",
    "timestamp",
    "actor",
    "action",
    "explanation"
  ],
  "properties": {
    "event_id": { "type": "string" },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "actor": {
      "type": "string",
      "enum": ["user", "agent", "generator", "rde", "policy", "runtime", "reviewer", "system"]
    },
    "task_contract_id": {
      "type": ["string", "null"]
    },
    "generator_output_id": {
      "type": ["string", "null"]
    },
    "structural_diff_id": {
      "type": ["string", "null"]
    },
    "semantic_delta_id": {
      "type": ["string", "null"]
    },
    "rde_result_id": {
      "type": ["string", "null"]
    },
    "policy_decision_id": {
      "type": ["string", "null"]
    },
    "execution_result_id": {
      "type": ["string", "null"]
    },
    "action": {
      "type": "string",
      "enum": [
        "create_contract",
        "generate_output",
        "run_structural_diff",
        "estimate_semantic_delta",
        "evaluate_rde",
        "make_policy_decision",
        "apply_change",
        "reject_change",
        "halt",
        "rollback",
        "request_human_review",
        "submit_human_review",
        "update_relation_store",
        "error"
      ]
    },
    "hash_before": {
      "type": ["string", "null"],
      "pattern": "^(sha256:[a-fA-F0-9]{64})$"
    },
    "hash_after": {
      "type": ["string", "null"],
      "pattern": "^(sha256:[a-fA-F0-9]{64})$"
    },
    "explanation": {
      "type": "string"
    },
    "payload": {
      "type": "object",
      "additionalProperties": true
    },
    "error": {
      "type": ["object", "null"],
      "properties": {
        "error_type": { "type": "string" },
        "message": { "type": "string" },
        "recoverable": { "type": "boolean" }
      },
      "additionalProperties": true
    }
  },
  "additionalProperties": false
}
```

## 4. Example

```json
{
  "event_id": "audit_001",
  "timestamp": "2026-05-04T00:00:00Z",
  "actor": "rde",
  "task_contract_id": "tc_001",
  "generator_output_id": "go_001",
  "structural_diff_id": "sdiff_001",
  "semantic_delta_id": null,
  "rde_result_id": "rde_001",
  "policy_decision_id": null,
  "execution_result_id": null,
  "action": "evaluate_rde",
  "hash_before": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "hash_after": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "explanation": "RDE classified the change as suspicious_drift because a protected claim changed and the generator self-report did not disclose it.",
  "payload": {
    "classification": "suspicious_drift",
    "risk_level": "high"
  },
  "error": null
}
```

## 5. Phase 1 Storage

Phase 1 stores AuditEvent records as JSONL.

Recommended path:

```text
audit/events.jsonl
```

Each line is one valid AuditEvent JSON object.

## 6. Required Audit Points

Phase 1 must record:

```text
- TaskContract creation
- GeneratorOutput creation or import
- StructuralDiff execution
- RDE evaluation
- PolicyDecision
- ExecutionResult or halt
```

## 7. RelationStore Usage

RelationStore must only update based on auditable events.

Examples:

```text
critical_corruption detected
  ↓
AuditEvent recorded
  ↓
RelationStore lowers trust or raises review threshold
```

```text
human reviewer confirms false positive
  ↓
AuditEvent recorded
  ↓
RelationStore adjusts drift pattern and threshold
```

## 8. Phase 1 Notes

AuditLog must be implemented before RelationStore update becomes meaningful.

For Phase 1, append-only JSONL is sufficient. Hash chaining and cryptographic signatures are Phase 2+ concerns.
