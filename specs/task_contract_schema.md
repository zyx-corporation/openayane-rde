---
title: "TaskContract Schema Specification"
version: "0.1"
date: "2026-05-05"
status: "public-schema-draft"
---

# TaskContract Schema Specification

## 0. Scope

This document specifies the public schema contract for `TaskContract`.

Normative source files:

```text
src/openayane_rde/core/models.py (TaskContract, TargetScope, OutputPolicy, ReviewPolicy)
schemas/task_contract.schema.json
```

## 1. Required and optional fields

### 1.1 Required

```text
contract_id: string
mode: enum
target_scope: object
requested_action: string
allowed_delta_m: string[]
forbidden_delta_m: string[]
protected_elements: enum[]
output_policy: object
review_policy: object
created_at: date-time
```

### 1.2 Optional

```text
relation_context_ref: string | null
metadata: object
```

## 2. Enum sets

### 2.1 mode

```text
preservation
creative
refactor
research
execution
```

### 2.2 protected_elements

```text
claims
definitions
numbers
dates
citations
references
constraints
headings
schema_keys
required_fields
types
function_signatures
public_api
imports
tests
safety_conditions
permissions
credentials
```

### 2.3 review_policy action sets

```text
preserved: auto_approve | approve_with_note | human_review
authorized_deviation: auto_approve | approve_with_note | human_review
benign_incidental_drift: approve_with_note | human_review
suspicious_drift: human_review | request_revision
critical_corruption: halt | rollback
```

## 3. Nested objects

### 3.1 target_scope

```text
files: string[]
symbols: string[]
sections: string[]
```

### 3.2 output_policy

```text
require_patch: boolean
require_change_report: boolean
require_uncertainty_report: boolean
```

### 3.3 review_policy

Object with keys:

```text
preserved
authorized_deviation
benign_incidental_drift
suspicious_drift
critical_corruption
```

All keys are required.

## 4. Validation and compatibility notes

- `additionalProperties` is forbidden at the top level and in nested contract policy objects.
- Contract consumers should treat unknown enum values as schema/version mismatch.
- Breaking changes must follow `docs/51_openayane_rde_release_compatibility_policy.md`.

## 5. Example

```json
{
  "contract_id": "tc_001",
  "mode": "preservation",
  "target_scope": {
    "files": ["docs/00_development_plan.md"],
    "symbols": [],
    "sections": ["phase-6"]
  },
  "requested_action": "clarify Phase 6 scope wording",
  "allowed_delta_m": ["sentence restructuring"],
  "forbidden_delta_m": ["number change"],
  "protected_elements": ["numbers", "citations"],
  "output_policy": {
    "require_patch": true,
    "require_change_report": true,
    "require_uncertainty_report": true
  },
  "review_policy": {
    "preserved": "auto_approve",
    "authorized_deviation": "approve_with_note",
    "benign_incidental_drift": "approve_with_note",
    "suspicious_drift": "human_review",
    "critical_corruption": "halt"
  },
  "relation_context_ref": null,
  "metadata": {},
  "created_at": "2026-05-05T00:00:00Z"
}
```
