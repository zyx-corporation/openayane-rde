---
title: "AuditEvent Schema Specification"
version: "0.1"
date: "2026-05-05"
status: "public-schema-draft"
---

# AuditEvent Schema Specification

## 0. Scope

This document specifies the public schema contract for `AuditEvent`.

Normative source files:

```text
src/openayane_rde/core/models.py (AuditEvent, AuditError)
schemas/audit_event.schema.json
```

## 1. Required and optional fields

### 1.1 Required

```text
event_id: string
timestamp: date-time
actor: enum
action: enum
explanation: string
```

### 1.2 Optional linkage IDs

```text
task_contract_id: string | null
generator_output_id: string | null
structural_diff_id: string | null
semantic_delta_id: string | null
rde_result_id: string | null
policy_decision_id: string | null
execution_result_id: string | null
```

### 1.3 Optional integrity and payload fields

```text
hash_before: "sha256:<64hex>" | null
hash_after: "sha256:<64hex>" | null
payload: object
error: object | null
```

## 2. Enum sets

### 2.1 actor

```text
user
agent
generator
rde
policy
runtime
reviewer
system
```

### 2.2 action

```text
create_contract
generate_output
run_structural_diff
estimate_semantic_delta
evaluate_rde
make_policy_decision
apply_change
reject_change
halt
rollback
request_human_review
submit_human_review
update_relation_store
error
execution_gate_evaluated
execution_blocked
execution_approved
execution_dry_run_completed
execution_completed
execution_failed
execution_timed_out
human_review_requested
human_review_decided
rollback_plan_created
rollback_completed
rollback_failed
semantic_evaluation_completed
```

## 3. Nested error object

If `error` is present:

```text
error_type: string
message: string
recoverable: boolean
```

`error` allows additional properties for implementation-specific diagnostics.

## 4. Validation and compatibility notes

- Top-level `additionalProperties` is forbidden.
- `hash_before` and `hash_after` must match `sha256:<64 hex digits>`.
- AuditEvent is structured audit evidence, not cryptographic tamper-proof proof.
- Breaking changes must follow `docs/51_openayane_rde_release_compatibility_policy.md`.

## 5. Example

```json
{
  "event_id": "audit_001",
  "timestamp": "2026-05-05T00:00:00Z",
  "actor": "rde",
  "task_contract_id": "tc_001",
  "generator_output_id": "go_001",
  "structural_diff_id": "sdiff_001",
  "semantic_delta_id": "sdelta_001",
  "rde_result_id": "rde_001",
  "policy_decision_id": "pd_001",
  "execution_result_id": null,
  "action": "evaluate_rde",
  "hash_before": null,
  "hash_after": null,
  "explanation": "RDE classification completed for contract tc_001.",
  "payload": {
    "classification": "suspicious_drift"
  },
  "error": null
}
```
