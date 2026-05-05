---
title: "OpenAyane RDE Core Specification"
version: "0.1"
date: "2026-05-05"
status: "public-spec-draft"
---

# OpenAyane RDE Core Specification

## 0. Purpose

This specification defines the public core vocabulary of OpenAyane RDE.

RDE stands for **Resonant Deviation Evaluator**. In OpenAyane, RDE is a meaning-change audit layer that evaluates how a generated output, document edit, code modification, or agent action changes meaning relative to an explicit contract, protected elements, evidence, relation history, and policy context.

RDE is not a generic quality score. It is not merely a textual diff. It is not the policy engine. It is not a safety filter by itself. It is not an LLM evaluator. It is a structured layer for classifying meaning change and drift risk.

## 1. Normative references

Read this document with:

```text
- docs/00_development_plan.md
- docs/37_openayane_rde_phase3_exit_report.md
- docs/40_openayane_rde_phase4_institution_bridge_spec.md
- docs/52_openayane_rde_phase5_completion_report.md
- docs/60_openayane_rde_phase6_issue_branch_plan.md
```

Implementation model names referenced here are primarily defined in:

```text
src/openayane_rde/core/models.py
```

This document is descriptive and normative for public terminology. It does not by itself change runtime behavior.

## 2. Core thesis

OpenAyane RDE treats generative or agentic output as a **meaning-changing operation**.

The central question is:

```text
Given an original state, a generated or executed change, and an explicit contract, what meaning changed, was that change allowed, what evidence supports the judgement, and what action should follow?
```

The informal symbol **ΔM** denotes this meaning change. ΔM is not limited to text edits. It may include structural change, semantic drift, self-report mismatch, policy-relevant side effects, or relation-context changes.

## 3. What RDE is not

RDE must not be collapsed into adjacent layers.

| Not RDE | Why |
|---|---|
| Diff | Diff identifies structural differences. RDE interprets differences against contract, evidence, and protected meaning. |
| Policy | Policy decides operational action. RDE classifies meaning change and risk. |
| Safety filter | A safety filter blocks or permits. RDE explains and classifies deviation. |
| LLM evaluator | An LLM may assist semantic evaluation, but model opinion is not the RDE authority. |
| Human review | Human review records institutional judgement. RDE supplies structured evidence and classification. |
| Institution Bridge | Institution Bridge checks authority and accountability. RDE does not grant authority. |

## 4. Core objects

### 4.1 TaskContract

`TaskContract` defines the expected transformation boundary for a non-execution evaluation path.

Core fields include:

```text
contract_id
mode
target_scope
requested_action
allowed_delta_m
forbidden_delta_m
protected_elements
output_policy
review_policy
relation_context_ref
metadata
created_at
```

A TaskContract makes explicit what is allowed, forbidden, protected, and review-sensitive.

RDE evaluates outputs relative to a TaskContract. Without a contract, RDE cannot distinguish a creative transformation from an unauthorized distortion.

### 4.2 GeneratorOutput

`GeneratorOutput` represents what a generator produced.

It includes:

```text
output_id
contract_id
output_type
payload
self_report
model_info
created_at
```

The generator's `self_report` is evidence, but not authoritative. RDE compares self-report claims against structural and semantic evidence.

### 4.3 StructuralDiff

`StructuralDiff` is the structured difference lens used by RDE.

It includes:

```text
diff_id
contract_id
domain
changed_nodes
added_nodes
deleted_nodes
moved_nodes
protected_element_changes
schema_violations
signature_changes
reference_breaks
self_report_mismatches
diff_confidence
metadata
created_at
```

StructuralDiff is not RDE itself. It is one of the primary evidence sources used by RDE.

### 4.4 SemanticDelta

`SemanticDelta` represents meaning-change candidates.

It includes:

```text
delta_id
contract_id
delta_m_score
changed_claims
changed_constraints
changed_definitions
changed_numbers
changed_references
changed_safety_conditions
semantic_equivalence_score
uncertainty
is_stub
semantic_mode
created_at
```

Current SemanticDelta support may be structural-baseline or stub-like depending on phase and mode. A semantic delta estimate must not be treated as full semantic equivalence proof.

### 4.5 RDEResult

`RDEResult` is the core RDE output.

It includes:

```text
result_id
contract_id
classification
resonance_score
preservation_score
authorization_score
risk_level
violated_constraints
suspicious_elements
required_action
explanation
score_details
evaluation_kind
evidence_basis
metadata
created_at
```

`evaluation_kind` tells what kind of evaluation occurred, such as pre-execution synthetic evaluation or post-structural evaluation.

`evidence_basis` tells what evidence the result used, such as tool-risk rules, execution contracts, structural diff, semantic delta, observed side effects, rollback result, human review decision, or LLM-assisted semantic evaluation.

This distinction prevents synthetic tool-risk evaluation from being mistaken for full structural or semantic RDE.

### 4.6 PolicyDecision

`PolicyDecision` maps RDE evidence into an operational action.

It includes:

```text
decision_id
contract_id
rde_result_id
action
rationale
institution_rule_id
institutional_rationale
metadata
created_at
```

PolicyDecision is not RDE classification. It is a decision derived from RDE and related context.

### 4.7 AuditEvent

`AuditEvent` records evidence and decision trace.

It includes:

```text
event_id
timestamp
actor
task_contract_id
generator_output_id
structural_diff_id
semantic_delta_id
rde_result_id
policy_decision_id
execution_result_id
action
hash_before
hash_after
explanation
payload
error
```

AuditEvent is the historical trace used by operators, RelationStore, review workflows, and later public evaluation.

Phase 5 does not claim cryptographic audit integrity. AuditEvent is structured audit evidence, not a tamper-proof guarantee.

### 4.8 RelationContext and RelationStore records

`RelationContext` and related store records represent relation-state evidence.

They include trust, stability, context affinity, drift patterns, and historical adjustment signals.

Relation state is not a moral score or a social ranking. It is a bounded operational signal used to adjust review thresholds and policy risk.

### 4.9 ExecutionTaskContract and execution evidence

Agent/tool execution is represented with execution-specific models such as:

```text
ToolCallRequest
ExecutionTaskContract
ToolCallRisk
ExecutionGateDecision
ExecutionGateEvaluation
ToolExecutionResult
PostExecutionDiff
RollbackPlan
RollbackResult
ReviewRequest
ReviewDecision
```

These extend RDE from document/code evaluation into bounded agent execution governance.

Execution evidence must preserve the distinction between:

```text
policy halt
RDE halt
runtime block
review rejection
institutional halt
```

## 5. Classification categories

The implemented `RDEClassification` values include:

```text
preserved
authorized_deviation
benign_incidental_drift
suspicious_drift
critical_corruption
creative_deviation
```

Public documentation may also use broader RDE review vocabulary:

```text
preserved
authorized transformation
inferred extension
suspicious drift
critical distortion
```

The mapping is conceptual rather than one-to-one in all contexts.

### 5.1 preserved

The protected intent, structure, or meaning is preserved.

### 5.2 authorized_deviation / authorized transformation

A change occurred, but it falls within the explicitly allowed transformation scope.

### 5.3 benign_incidental_drift

A minor drift occurred that does not currently require halt, but should remain visible.

### 5.4 creative_deviation

A creative or exploratory change occurred within a context where such deviation is expected or permitted.

### 5.5 suspicious_drift

A change appears meaningfully divergent, under-evidenced, inconsistent with the contract, or risky enough to require revision or human review.

### 5.6 critical_corruption / critical distortion

A change violates protected elements, safety constraints, required claims, schema invariants, or execution boundaries in a way that should halt or roll back.

## 6. Evaluation kinds and evidence basis

RDE output should distinguish evaluation timing/type from evidence source.

`evaluation_kind` answers:

```text
What kind of evaluation was performed?
```

`evidence_basis` answers:

```text
What evidence supported the judgement?
```

Examples:

| Situation | evaluation_kind | evidence_basis |
|---|---|---|
| Pre-tool gate synthetic check | `pre_synthetic` | `tool_risk_rule`, `execution_contract` |
| Post-diff document evaluation | `post_structural` | `structural_diff`, `semantic_delta` |
| Post-execution check with rollback | `post_structural` | `observed_side_effects`, `rollback_result` |
| Human-reviewed path | varies | `human_review_decision` |

This separation is required for auditability.

## 7. Required action

RDE may recommend or require actions such as:

```text
approve
approve_with_notes
request_revision
human_review
halt
rollback
```

The presence of a required action does not collapse RDE into Policy. Policy must still translate classification, relation context, institution rules, and operational context into an executable decision.

## 8. Relation to Institution Bridge

The Institution Bridge introduced in Phase 4 evaluates authority and accountability. It consumes RDE and policy evidence, but does not replace them.

For example:

```text
RDE may classify a change as suspicious_drift.
Policy may require human_review.
Institution Bridge may determine whether the reviewer has authority to accept the consequence.
```

These are separate judgements.

## 9. Research and public specification boundary

Phase 6 turns the implemented system into public specification, benchmark fixtures, evaluation reports, and technical-report material.

Phase 6 must not overclaim:

```text
- production readiness
- high assurance runtime safety
- cryptographic audit integrity
- complete semantic equivalence checking
- universal benchmark validity
- legal or compliance guarantee
```

## 10. RDE differential review of this specification

### 10.1 Preserved elements

This specification preserves the implemented separation between RDE, Policy, Runtime, Human Review, Institution Bridge, RelationStore, and AuditLog.

### 10.2 Authorized transformations

Internal model names and development-phase concepts are transformed into public specification vocabulary.

### 10.3 Inferred extensions

The specification introduces public explanatory language such as meaning-change audit layer and public classification descriptions. These clarify the implementation but do not add new runtime behavior.

### 10.4 Unresolved elements

The following remain unresolved:

```text
- full semantic equivalence specification
- benchmark validity beyond fixture scope
- cryptographic audit guarantees
- production identity or PoP proof
- public standardization process
```

### 10.5 Drift risks

Key risks:

```text
- treating public vocabulary as stronger than implemented behavior
- treating SemanticDelta as complete semantic understanding
- treating AuditEvent as tamper-proof audit
- treating RDE as Policy or Institution authority
- treating benchmark fixtures as general empirical validation
```

### 10.6 Next update policy

P6-2 schema specifications must align with this vocabulary and with implemented Pydantic / JSON schema fields.

## 11. Document history

| Version | Date | Note |
|---|---|---|
| 0.1 | 2026-05-05 | Initial public RDE Core specification for P6-1. |
