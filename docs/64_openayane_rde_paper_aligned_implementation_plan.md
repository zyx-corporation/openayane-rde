# OpenAyane RDE Paper-Aligned Implementation Plan

## 1. Purpose

This document defines the next implementation policy for OpenAyane RDE after the M-RDE-G0 pre-gateway evaluate contract baseline.

The purpose is to translate the RDE position paper into implementation constraints without reducing RDE to a generic LLM judge, policy filter, or scalar quality score.

RDE must be implemented as a semantic-change audit layer: it records what is preserved, what is authorized, what is inferred, what remains unresolved, and where suspicious drift or critical distortion may have occurred.

This document also defines how the RDE implementation should be introduced into the Gateway path. The first Gateway integration stage is compare-only. RDE classifications must be observable through trace, audit, and explain outputs before they are allowed to influence execution control.

## 2. Design Position

### 2.1 RDE is not a policy filter

RDE does not directly decide whether an action is allowed, blocked, rolled back, or escalated. It evaluates semantic deviation between a source state and a generated or modified output under a declared task, risk context, and reference anchor.

Policy Bridge is responsible for converting RDE findings into operational decisions.

Therefore, the implementation must keep these layers separate:

```text
Structural Diff / Semantic Evidence
  -> RDE Evaluation
  -> Recommended Action
  -> Policy Bridge Decision
  -> Execution Control
```

The `recommended_action` field is advisory until a later Gateway enforcement milestone explicitly enables it.

### 2.2 RDE is not LLM-as-a-judge

An LLM evaluator may assist classification, but it is not the definition of RDE.

RDE implementation must allow multiple evaluator kinds:

- rule-based evaluator
- LLM-assisted evaluator
- human annotation adapter
- hybrid evaluator

The final audit payload must record the evaluator kind and version.

### 2.3 RDE is not a scalar score

RDE findings must not be collapsed into a single quality score. A scalar may exist as a derived severity or confidence field, but the primary structure must remain multi-axis, evidence-bearing, and auditable.

## 3. Paper-Aligned RDE Core Concepts

### 3.1 Required contextual inputs

Every RDE evaluation should be grounded by the following context whenever available:

```text
source
output
task
risk_context
reference_anchor
trace_id
contract_version
```

`source` is not treated as an absolute truth. It is a declared working anchor for the evaluation. If source authority is ambiguous, this must be represented in the evaluation result instead of hidden.

### 3.2 Six paper-aligned labels

The paper-aligned internal RDE labels are:

```text
preserved
authorized_transformation
inferred_extension
unresolved_gap
suspicious_drift
critical_distortion
```

These are evaluation labels, not direct policy actions.

### 3.3 Mapping to existing implementation labels

Existing implementation labels may continue to exist for backward compatibility, but they should be treated as adapter-facing labels.

| Paper-aligned label | Existing / adapter-facing label | Typical action hint |
|---|---|---|
| `preserved` | `preserved` | `approve` |
| `authorized_transformation` | `permitted_deviation` | `approve` or `warn` |
| `inferred_extension` | `minor_side_effect` or `creative_deviation` | `warn` or `review` |
| `unresolved_gap` | `questionable_drift` | `review` |
| `suspicious_drift` | `questionable_drift` | `review` or `reject` |
| `critical_distortion` | `critical_corruption` | `reject` or `rollback_candidate` |

The mapping must remain explicit and testable. It must not be embedded implicitly in Gateway control flow.

## 4. Seven-Axis Evaluation Model

RDE should evaluate semantic change through seven axes. These axes are not independent proof dimensions. They are structured lenses for identifying where meaning has changed.

```text
claim_strength
uncertainty
intent
responsibility
value_structure
institutional_implication
context_affinity
```

Each axis evaluation should preserve the following fields:

```text
axis
direction
severity
confidence
evidence
explanation
```

Recommended enum shape:

```python
@dataclass
class AxisEvaluation:
    axis: Literal[
        "claim_strength",
        "uncertainty",
        "intent",
        "responsibility",
        "value_structure",
        "institutional_implication",
        "context_affinity",
    ]
    direction: Literal[
        "preserved",
        "increased",
        "decreased",
        "shifted",
        "lost",
        "unclear",
    ]
    severity: Literal["none", "low", "medium", "high", "critical"]
    confidence: float
    evidence: list[str]
    explanation: str
```

## 5. RDEEvaluation Schema Direction

The next schema-level implementation should introduce or extend an evaluation payload equivalent to the following structure.

```python
@dataclass
class RDEEvaluation:
    evaluation_id: str
    trace_id: str
    source_id: str | None
    task: str
    risk_context: str | None
    reference_anchor: str | None

    structural_diff: StructuralDiffResult | None
    axis_evaluations: list[AxisEvaluation]

    primary_label: Literal[
        "preserved",
        "authorized_transformation",
        "inferred_extension",
        "unresolved_gap",
        "suspicious_drift",
        "critical_distortion",
    ]

    risk_flags: list[str]
    criticality: Literal["none", "low", "medium", "high", "critical"]
    confidence: float

    recommended_action: Literal[
        "approve",
        "warn",
        "review",
        "reject",
        "rollback_candidate",
    ]
    explanation: str
    evidence_spans: list[EvidenceSpan]

    evaluator_kind: Literal["rule", "llm", "human", "hybrid"]
    evaluator_version: str
```

This schema should be introduced in a backward-compatible way. Existing `RDEResult` payloads must not be broken without a compatibility note and schema migration plan.

## 6. Risk Flags

Risk flags are evidence-oriented indicators, not final judgments. The first deterministic rule evaluator should target the following flags:

```text
claim_strength_inflation
uncertainty_loss
responsibility_shift
value_simplification
institutional_implication_loss
context_drift
theoretical_reduction
source_anchor_ambiguity
self_report_mismatch
```

These flags should be emitted with evidence spans whenever possible.

## 7. Evaluator Implementation Order

### 7.1 Stage A: Schema and audit first

The first implementation step is not `RDEClassifier`. It is the schema and audit envelope.

Required outputs:

- paper-aligned labels
- seven-axis evaluation container
- risk flags
- evidence spans
- evaluator kind and version
- explicit mapping to `recommended_action`

### 7.2 Stage B: Deterministic red-flag evaluator

The first evaluator should be deterministic and conservative. It should detect obvious structural and linguistic risk signals, such as uncertainty loss, claim strengthening, responsibility shifts, and deleted references.

It does not need to prove semantic distortion. It only needs to surface evidence for RDE classification and human review.

### 7.3 Stage C: LLM-assisted evaluator

The LLM evaluator may be added after deterministic evidence extraction exists.

Constraints:

- Input should be structural diff plus evidence candidates, not only raw full text.
- Output must be JSON-schema constrained.
- LLM output must record evaluator version and prompt version.
- LLM output must not be the only audit artifact.
- Rule/LLM disagreement must be preserved.

### 7.4 Stage D: Human review adapter

Human review should be represented as a first-class evaluator kind. Human review does not erase RDE uncertainty; it records an institutional decision over the evidence.

## 8. Gateway Integration Plan

### 8.1 First Gateway milestone: compare-only

The first Gateway milestone must be compare-only.

```text
M-GW-RDE-1: Gateway compare-only integration
```

Completion criteria:

- Gateway can call the RDE evaluation path.
- Legacy Gateway behavior remains the effective behavior.
- RDE result is stored in trace metadata.
- RDE result is stored in audit events.
- Explain output can show legacy vs RDE comparison.
- RDE failure does not block the Gateway when fail-open is enabled.
- `recommended_action` is informational only.

### 8.2 Gateway mode settings

Gateway integration should use explicit modes.

```text
OPENAYANE_RDE_MODE=disabled|compare|rde
OPENAYANE_RDE_FAIL_OPEN=true|false
OPENAYANE_RDE_AUDIT_ENABLED=true|false
OPENAYANE_RDE_EXPLAIN_ENABLED=true|false
```

Initial default:

```text
OPENAYANE_RDE_MODE=disabled
OPENAYANE_RDE_FAIL_OPEN=true
```

### 8.3 HybridEvaluator role

`HybridEvaluator` should preserve both outputs.

```text
legacy_result
rde_result
agreement
disagreement_type
effective_result
```

In compare mode, `effective_result` must remain `legacy_result`.

### 8.4 Mismatch taxonomy

Gateway compare mode should record at least the following mismatch patterns:

```text
legacy_allow_rde_review
legacy_allow_rde_reject
legacy_block_rde_preserved
legacy_low_quality_rde_preserved
legacy_high_quality_rde_suspicious
rde_error_legacy_continued
```

These mismatches are the primary evidence for later enforcement decisions.

## 9. Enforcement Gate Conditions

RDE must not be promoted from compare-only to enforcement solely because the code path exists.

Minimum conditions before enforcement:

- compare-mode traces have been collected
- mismatch taxonomy has been reviewed
- false-positive and false-negative candidates have been documented
- `critical_distortion` / `critical_corruption` cases have human-reviewed examples
- rollback path is tested but disabled by default
- known limitations have been updated

Initial enforcement, if enabled, should be limited to `critical_distortion` or implementation-equivalent `critical_corruption`, and should initially route to review rather than automatic rollback.

## 10. RelationStore Update Policy

RDE observations should not immediately mutate trust/stability in the first Gateway integration stage.

Initial persistence should use separate observation fields or audit events:

```text
rde_observations
rde_mismatch_count
rde_critical_count
last_rde_evaluation
```

Only after compare-mode evaluation should RDE classification influence trust updates.

## 11. Documentation and Compatibility Requirements

Any PR that changes public RDE schema, CLI, API, or Gateway-facing behavior must update:

- `CHANGELOG.md`
- schema documentation
- known limitations
- testing policy if expectations change

Classification changes must state whether they are:

- paper-aligned internal changes
- adapter-facing compatibility changes
- policy/action mapping changes

## 12. RDE Differential Review

### Preserved elements

- RDE remains a semantic-change audit layer.
- RDE remains distinct from Policy Bridge and execution control.
- RDE labels remain distinct from operational actions.
- Source meaning is treated as a declared working anchor, not an absolute truth.
- Evaluation remains multi-axis and evidence-bearing.

### Authorized transformations

- Paper concepts are translated into JSON/Python schema fields.
- RDE labels are mapped to adapter-facing labels for backward compatibility.
- Gateway integration begins as compare-only observability.

### Inferred extensions

- `evaluator_kind` and `evaluator_version` are added to preserve provenance.
- `evidence_spans` are introduced to support audit and review.
- `mismatch_taxonomy` is introduced to guide future enforcement decisions.

### Unresolved gaps

- Exact source-authority resolution remains outside this milestone.
- LLM evaluator reliability remains unproven.
- Human review calibration remains future work.
- RelationStore trust update policy remains deferred.

### Suspicious drift risks

- Treating RDE as a direct policy filter.
- Treating LLM evaluator output as RDE itself.
- Collapsing seven-axis evaluation into a single score.
- Automatically rolling back on `critical_distortion` before compare-mode evidence exists.
- Hiding rule/LLM disagreement.

### Next update policy

The next implementation PR should introduce the schema/audit envelope first, then deterministic risk-flag extraction. Gateway enforcement must remain out of scope until compare-only evidence exists.

## 13. Immediate Follow-up Issues

Recommended issue decomposition:

```text
1. Add paper-aligned RDEEvaluation schema extension
2. Add AxisEvaluation and EvidenceSpan schema objects
3. Add deterministic red-flag evaluator
4. Add paper-label to adapter-label mapping tests
5. Add Gateway compare-only adapter
6. Add RDE result to trace metadata
7. Add RDE audit event for compare mode
8. Add explain output for legacy/RDE comparison
9. Add mismatch taxonomy report
10. Update known limitations after compare-mode traces
```

## 14. Milestone Summary

```text
M-RDE-PAPER-1:
  Paper-aligned schema and audit envelope

M-RDE-PAPER-2:
  Deterministic red-flag evaluator

M-RDE-PAPER-3:
  LLM-assisted evaluator with schema-constrained output

M-GW-RDE-1:
  Gateway compare-only integration

M-GW-RDE-2:
  Audit/explain observability

M-GW-RDE-3:
  Limited review-only Policy Bridge connection
```

The guiding principle is simple: RDE must first become a reliable mirror before it becomes a gate.

Closes #129
