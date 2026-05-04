# GeneratorOutput JSON Schema Specification

## 1. Purpose

`GeneratorOutput` represents the raw output produced by a Generator under a `TaskContract`.

In OpenAyane, the Generator is not trusted as the final authority. Its output must be inspected by Structural Diff, Semantic Delta, RDE Core, and Policy Bridge before being applied.

`GeneratorOutput` contains two important parts:

```text
payload:
  actual generated text, patch, plan, or tool call

self_report:
  Generator's own claim about what changed and what did not change
```

The self-report is not treated as truth. Instead, mismatches between `self_report` and actual diff are treated as risk signals.

```text
actual_diff - generator_self_report = unrecognized drift
```

## 2. Design Principles

### 2.1 Generator is not final authority

A Generator may propose a transformation, but it does not approve or apply it.

### 2.2 Self-report is auditable evidence

The self-report is useful because it exposes what the Generator thinks it changed. If the actual diff contradicts the self-report, OpenAyane records that as a possible Silent ΔM signal.

### 2.3 Output must be linked to a TaskContract

Every `GeneratorOutput` must reference the `contract_id` of the TaskContract that produced it.

## 3. JSON Schema Draft

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/zyx-corporation/openayane-rde/schemas/generator_output.schema.json",
  "title": "GeneratorOutput",
  "type": "object",
  "required": [
    "output_id",
    "contract_id",
    "output_type",
    "payload",
    "self_report",
    "model_info",
    "created_at"
  ],
  "properties": {
    "output_id": {
      "type": "string",
      "description": "Unique generator output identifier."
    },
    "contract_id": {
      "type": "string",
      "description": "TaskContract identifier that produced this output."
    },
    "output_type": {
      "type": "string",
      "enum": ["full_text", "patch", "plan", "tool_call"]
    },
    "payload": {
      "description": "Generated content, patch, plan, or tool-call payload.",
      "oneOf": [
        { "type": "string" },
        { "type": "object", "additionalProperties": true },
        { "type": "array" }
      ]
    },
    "self_report": {
      "type": "object",
      "required": [
        "changed_elements",
        "unchanged_elements",
        "added_elements",
        "deleted_elements",
        "semantic_risk_notes",
        "uncertainty_notes"
      ],
      "properties": {
        "changed_elements": {
          "type": "array",
          "items": { "type": "string" }
        },
        "unchanged_elements": {
          "type": "array",
          "items": { "type": "string" }
        },
        "added_elements": {
          "type": "array",
          "items": { "type": "string" }
        },
        "deleted_elements": {
          "type": "array",
          "items": { "type": "string" }
        },
        "semantic_risk_notes": {
          "type": "array",
          "items": { "type": "string" }
        },
        "uncertainty_notes": {
          "type": "array",
          "items": { "type": "string" }
        }
      },
      "additionalProperties": false
    },
    "model_info": {
      "type": "object",
      "required": ["provider", "model"],
      "properties": {
        "provider": {
          "type": "string",
          "enum": ["openai", "anthropic", "google", "local", "tool", "mock", "unknown"]
        },
        "model": {
          "type": "string"
        },
        "temperature": {
          "type": ["number", "null"]
        },
        "metadata": {
          "type": "object",
          "additionalProperties": true
        }
      },
      "additionalProperties": false
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
  "output_id": "go_001",
  "contract_id": "tc_001",
  "output_type": "patch",
  "payload": "--- original.md\n+++ revised.md\n@@ ...",
  "self_report": {
    "changed_elements": ["sentence structure", "redundant wording"],
    "unchanged_elements": ["claims", "citations", "numbers"],
    "added_elements": [],
    "deleted_elements": [],
    "semantic_risk_notes": [],
    "uncertainty_notes": ["No semantic change intended."]
  },
  "model_info": {
    "provider": "mock",
    "model": "manual-test-generator",
    "temperature": null,
    "metadata": {}
  },
  "created_at": "2026-05-04T00:00:00Z"
}
```

## 5. Validation Requirements

- `output_id` must be unique.
- `contract_id` must correspond to an existing TaskContract.
- `self_report` must be present even for mock outputs.
- `output_type` must match the payload interpretation.
- Tool calls must be represented as structured objects when `output_type` is `tool_call`.

## 6. RDE Usage

RDE and Structural Diff use GeneratorOutput in two ways:

```text
1. Analyze payload against original state.
2. Compare self_report against actual structural and semantic differences.
```

Mismatch examples:

```text
self_report says numbers unchanged
actual diff detects changed number
=> suspicious drift or critical corruption depending on TaskContract
```

```text
self_report omits deleted citation
actual diff detects citation removal
=> suspicious drift or critical corruption
```

## 7. Phase 1 Notes

For Phase 1 MVP, GeneratorOutput may be produced by:

```text
- a mock generator
- manual fixture
- local script
- LLM output copied into test fixture
```

Direct integration with external LLM providers is not required in Phase 1.
