# StructuralDiff JSON Schema Specification

## 1. Purpose

`StructuralDiff` represents the structured difference between an original state and a generated state.

It is not the same as RDE. Structural Diff is a structured lens that turns the Generator's reconstructed output into inspectable objects.

```text
Surface diff:
  line-level or token-level change

StructuralDiff:
  document, schema, or AST-level change

RDE:
  evaluates whether the detected changes are authorized, suspicious, or corruptive
```

## 2. Design Principles

### 2.1 Structural Diff is not semantic judgment

Structural Diff detects structural changes. It does not decide whether those changes are acceptable.

### 2.2 Domain-specific plugins

Structural Diff is implemented as a domain plugin system.

Phase 1 domains:

```text
- markdown
- json
- python
```

Future domains:

```text
- yaml
- typescript
- sql
- latex
- openapi
- terraform
- kubernetes
```

### 2.3 Protected element tracking

Changes to elements listed in `TaskContract.protected_elements` must be collected in `protected_element_changes`.

### 2.4 Self-report mismatch detection

Structural Diff must compare actual changes against `GeneratorOutput.self_report` when possible.

## 3. JSON Schema Draft

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/zyx-corporation/openayane-rde/schemas/structural_diff.schema.json",
  "title": "StructuralDiff",
  "type": "object",
  "required": [
    "diff_id",
    "contract_id",
    "domain",
    "changed_nodes",
    "added_nodes",
    "deleted_nodes",
    "moved_nodes",
    "protected_element_changes",
    "schema_violations",
    "signature_changes",
    "reference_breaks",
    "self_report_mismatches",
    "diff_confidence",
    "created_at"
  ],
  "properties": {
    "diff_id": { "type": "string" },
    "contract_id": { "type": "string" },
    "domain": {
      "type": "string",
      "enum": ["markdown", "json", "python", "generic"]
    },
    "changed_nodes": {
      "type": "array",
      "items": { "$ref": "#/$defs/diff_node" }
    },
    "added_nodes": {
      "type": "array",
      "items": { "$ref": "#/$defs/diff_node" }
    },
    "deleted_nodes": {
      "type": "array",
      "items": { "$ref": "#/$defs/diff_node" }
    },
    "moved_nodes": {
      "type": "array",
      "items": { "$ref": "#/$defs/diff_node" }
    },
    "protected_element_changes": {
      "type": "array",
      "items": { "$ref": "#/$defs/protected_change" }
    },
    "schema_violations": {
      "type": "array",
      "items": { "$ref": "#/$defs/violation" }
    },
    "signature_changes": {
      "type": "array",
      "items": { "$ref": "#/$defs/diff_node" }
    },
    "reference_breaks": {
      "type": "array",
      "items": { "$ref": "#/$defs/violation" }
    },
    "self_report_mismatches": {
      "type": "array",
      "items": { "$ref": "#/$defs/self_report_mismatch" }
    },
    "diff_confidence": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0
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
    "diff_node": {
      "type": "object",
      "required": ["path", "kind", "before", "after", "description"],
      "properties": {
        "path": { "type": "string" },
        "kind": { "type": "string" },
        "before": {},
        "after": {},
        "description": { "type": "string" },
        "risk_hint": {
          "type": "string",
          "enum": ["low", "medium", "high", "critical", "unknown"]
        }
      },
      "additionalProperties": true
    },
    "protected_change": {
      "type": "object",
      "required": ["element", "path", "change_type", "description"],
      "properties": {
        "element": { "type": "string" },
        "path": { "type": "string" },
        "change_type": {
          "type": "string",
          "enum": ["changed", "added", "deleted", "moved"]
        },
        "description": { "type": "string" },
        "risk_hint": {
          "type": "string",
          "enum": ["low", "medium", "high", "critical", "unknown"]
        }
      },
      "additionalProperties": false
    },
    "violation": {
      "type": "object",
      "required": ["path", "violation_type", "description"],
      "properties": {
        "path": { "type": "string" },
        "violation_type": { "type": "string" },
        "description": { "type": "string" },
        "risk_hint": {
          "type": "string",
          "enum": ["low", "medium", "high", "critical", "unknown"]
        }
      },
      "additionalProperties": true
    },
    "self_report_mismatch": {
      "type": "object",
      "required": ["reported", "actual", "description"],
      "properties": {
        "reported": { "type": "string" },
        "actual": { "type": "string" },
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

## 4. Domain Requirements

### 4.1 Markdown

Must detect:

```text
- heading additions/deletions/moves
- paragraph changes
- definition changes
- citation deletion or mutation
- link changes
- table changes
- code block changes
- number changes
- date changes
```

Protected elements frequently used in Markdown:

```text
claims
definitions
numbers
dates
citations
references
headings
constraints
```

### 4.2 JSON

Must detect:

```text
- key addition/deletion/change
- type changes
- required field deletion
- schema violations
- array length changes
- nullability changes
```

Protected elements frequently used in JSON:

```text
schema_keys
required_fields
types
constraints
```

### 4.3 Python

Must detect:

```text
- import changes
- function signature changes
- class definition changes
- control flow changes
- exception handling changes
- public API changes
- test deletion or weakening
```

Protected elements frequently used in Python:

```text
function_signatures
public_api
imports
tests
safety_conditions
permissions
credentials
```

## 5. Example

```json
{
  "diff_id": "sdiff_001",
  "contract_id": "tc_001",
  "domain": "markdown",
  "changed_nodes": [
    {
      "path": "/sections/2/paragraphs/3",
      "kind": "paragraph",
      "before": "RDE is not a policy filter.",
      "after": "RDE can be used as a policy filter.",
      "description": "Claim changed from non-identity to possible identity.",
      "risk_hint": "high"
    }
  ],
  "added_nodes": [],
  "deleted_nodes": [],
  "moved_nodes": [],
  "protected_element_changes": [
    {
      "element": "claims",
      "path": "/sections/2/paragraphs/3",
      "change_type": "changed",
      "description": "Protected claim changed.",
      "risk_hint": "high"
    }
  ],
  "schema_violations": [],
  "signature_changes": [],
  "reference_breaks": [],
  "self_report_mismatches": [
    {
      "reported": "claims unchanged",
      "actual": "claim changed",
      "description": "Generator self-report conflicts with actual diff.",
      "risk_hint": "high"
    }
  ],
  "diff_confidence": 0.92,
  "metadata": {},
  "created_at": "2026-05-04T00:00:00Z"
}
```

## 6. Phase 1 Notes

Phase 1 should prioritize structural detection over semantic completeness.

The objective is not to perfectly understand all meaning. The objective is to surface structural changes that may indicate unauthorized semantic drift.

Required Phase 1 implementations:

```text
MarkdownDiff
JsonDiff
PythonAstDiff
self_report_mismatch detection
protected_element_changes detection
```
