# TaskContract JSON Schema Specification

## 1. Purpose

`TaskContract` is the central contract object shared by the Generator, Structural Diff Engine, Semantic Delta Engine, RDE Core, Policy Bridge, AuditLog, and RelationStore.

Its role is to convert an ambiguous natural-language instruction into an explicit and auditable transformation contract.

`TaskContract` defines:

- what the user or agent requested,
- what semantic change is allowed,
- what semantic change is forbidden,
- which elements must be protected,
- which output format is required,
- which review policy should be applied,
- which relation context was used when building the contract.

In OpenAyane, the Generator does not receive an unconstrained instruction. It receives a `TaskContract`.

## 2. Design Principles

### 2.1 Contract before generation

The contract must be created before invoking any Generator.

```text
Raw instruction
  ↓
Intent Parser
  ↓
RelationContext Loader
  ↓
Task Contract Builder
  ↓
Generator Adapter
```

### 2.2 Evaluation reference

The contract is not only a Generator instruction. It is also the reference object against which RDE evaluates generated changes.

### 2.3 Explicit delta boundary

The contract must separate:

```text
allowed_delta_m:
  changes explicitly permitted

forbidden_delta_m:
  changes explicitly prohibited

protected_elements:
  elements that must be preserved unless explicitly authorized
```

### 2.4 Relation-aware contract generation

If RelationStore indicates past drift patterns, document fragility, or generator reliability issues, the Task Contract Builder may strengthen protected elements or review policies.

## 3. JSON Schema Draft

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/zyx-corporation/openayane-rde/schemas/task_contract.schema.json",
  "title": "TaskContract",
  "type": "object",
  "required": [
    "contract_id",
    "mode",
    "target_scope",
    "requested_action",
    "allowed_delta_m",
    "forbidden_delta_m",
    "protected_elements",
    "output_policy",
    "review_policy",
    "created_at"
  ],
  "properties": {
    "contract_id": {
      "type": "string",
      "description": "Unique contract identifier. UUID recommended."
    },
    "mode": {
      "type": "string",
      "enum": ["preservation", "creative", "refactor", "research", "execution"]
    },
    "target_scope": {
      "type": "object",
      "required": ["files", "symbols", "sections"],
      "properties": {
        "files": {
          "type": "array",
          "items": { "type": "string" }
        },
        "symbols": {
          "type": "array",
          "items": { "type": "string" }
        },
        "sections": {
          "type": "array",
          "items": { "type": "string" }
        }
      },
      "additionalProperties": false
    },
    "requested_action": {
      "type": "string"
    },
    "allowed_delta_m": {
      "type": "array",
      "items": { "type": "string" }
    },
    "forbidden_delta_m": {
      "type": "array",
      "items": { "type": "string" }
    },
    "protected_elements": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "claims",
          "definitions",
          "numbers",
          "dates",
          "citations",
          "references",
          "constraints",
          "headings",
          "schema_keys",
          "required_fields",
          "types",
          "function_signatures",
          "public_api",
          "imports",
          "tests",
          "safety_conditions",
          "permissions",
          "credentials"
        ]
      }
    },
    "output_policy": {
      "type": "object",
      "required": ["require_patch", "require_change_report", "require_uncertainty_report"],
      "properties": {
        "require_patch": { "type": "boolean" },
        "require_change_report": { "type": "boolean" },
        "require_uncertainty_report": { "type": "boolean" }
      },
      "additionalProperties": false
    },
    "review_policy": {
      "type": "object",
      "required": [
        "preserved",
        "authorized_deviation",
        "benign_incidental_drift",
        "suspicious_drift",
        "critical_corruption"
      ],
      "properties": {
        "preserved": {
          "type": "string",
          "enum": ["auto_approve", "approve_with_note", "human_review"]
        },
        "authorized_deviation": {
          "type": "string",
          "enum": ["auto_approve", "approve_with_note", "human_review"]
        },
        "benign_incidental_drift": {
          "type": "string",
          "enum": ["approve_with_note", "human_review"]
        },
        "suspicious_drift": {
          "type": "string",
          "enum": ["human_review", "request_revision"]
        },
        "critical_corruption": {
          "type": "string",
          "enum": ["halt", "rollback"]
        }
      },
      "additionalProperties": false
    },
    "relation_context_ref": {
      "type": ["string", "null"]
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
  "additionalProperties": false
}
```

## 4. Example

```json
{
  "contract_id": "tc_001",
  "mode": "preservation",
  "target_scope": {
    "files": ["paper/openayane_implementation_plan_final_ja.tex"],
    "symbols": [],
    "sections": ["OpenAyaneの実装フロー"]
  },
  "requested_action": "Improve readability while preserving claims and citations.",
  "allowed_delta_m": [
    "sentence restructuring",
    "minor wording improvements",
    "redundancy removal"
  ],
  "forbidden_delta_m": [
    "claim change",
    "definition change",
    "citation removal",
    "numeric change"
  ],
  "protected_elements": [
    "claims",
    "definitions",
    "numbers",
    "citations",
    "references"
  ],
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
  "metadata": {
    "domain": "paper",
    "language": "ja"
  },
  "created_at": "2026-05-04T00:00:00Z"
}
```

## 5. Validation Requirements

- `contract_id` must be unique.
- `mode` must be one of the defined modes.
- `protected_elements` must not be empty for preservation, refactor, research, or execution modes.
- `forbidden_delta_m` should not be empty in preservation mode.
- If `mode` is `execution`, `permissions` and `safety_conditions` should be included in `protected_elements`.
- If `mode` is `creative`, protected elements still apply.

## 6. Phase 1 Notes

For Phase 1 MVP, `TaskContract` may be manually authored or generated by a simple rule-based builder. Full automatic intent-to-contract conversion is not required.

However, all Phase 1 components must accept `TaskContract` as the canonical evaluation reference.
