---
title: "OpenAyane RDE Core — Public specification"
version: "0.1"
status: "draft"
date: "2026-05-06"
---

# OpenAyane RDE Core — Public specification

This document defines the **public meaning** of the Resonant Deviation Evaluator (RDE) layer in OpenAyane RDE. It is aligned with the Python types in `openayane_rde.core.models` unless an explicit exception is noted.

## 1. Role of RDE

**RDE is a meaning-change audit layer.** It observes transformations produced by generators, editors, agents, or tools, compares **actual structural and semantic evidence** against a declared **TaskContract**, and emits a structured classification (`RDEResult`) together with evidence pointers—not a final business or deployment decision by itself.

RDE answers: *what kind of deviation from the contracted intent and structure appears to have occurred, and with what risk?*

Execution control (approve, halt, rollback, human review routing) is expressed through **Policy** and runtime layers that consume `RDEResult`; RDE does not substitute for organizational policy, institutional rules, or safety filters.

## 2. Semantic change (ΔM)

**ΔM (delta M)** denotes a shift in meaning-bearing content relative to a baseline state and an allowed transformation envelope. RDE does not claim to compute a unique real-valued “true semantics” for arbitrary artifacts. In implementation, ΔM is approximated by:

- **StructuralDiff** — structured edits (Markdown, JSON, Python AST, etc.).
- **SemanticDelta** — structured estimates of meaning-bearing shifts (including stub / structural-baseline modes in early phases).
- **Self-report checks** — comparison of generator `SelfReport` against observed diff evidence.

This specification does **not** assert full semantic equivalence for arbitrary natural-language or code artifacts; see section 8.

## 3. Core artefacts (names follow `openayane_rde.core.models`)

| Concept | Purpose |
|--------|---------|
| **TaskContract** | Declares mode, target scope, requested action, allowed/forbidden ΔM descriptions (`allowed_delta_m`, `forbidden_delta_m`), protected element kinds, output requirements, and per-classification review hooks (`ReviewPolicy`). |
| **GeneratorOutput** | Payload plus **SelfReport** (generator’s own accounting of edits) and **ModelInfo**; self-report is **advisory** input to RDE, not ground truth. |
| **StructuralDiff** | Domain-tagged structural comparison result: changed/added/deleted/moved nodes, protected-element changes, schema violations, signature changes, reference breaks, **self_report_mismatches**. |
| **SemanticDelta** | Estimate of meaning-bearing change (`delta_m_score`, changed claims/constraints/definitions/…); may remain stub or structural-baseline depending on phase and configuration. |
| **RDEResult** | **Classification** (`RDEClassification`), scores, risk level, violated constraints, suspicious elements, **required_action** (advisory to policy), explanation, optional score breakdown, **evaluation_kind**, **evidence_basis**. |
| **PolicyDecision** | Maps evaluation outcomes to an operator action (`PolicyActionKind`) with rationale; institution-layer fields are supplements and **must not** replace `RDEResult.classification`. |
| **AuditEvent** | Append-only audit record correlating actors, actions, and linked artefact IDs (`task_contract_id`, `generator_output_id`, `structural_diff_id`, etc.). |

## 4. What RDE is **not**

RDE is explicitly **not** any of the following when taken alone:

| Misidentification | Correct separation |
|-------------------|-------------------|
| **Plain textual diff** | StructuralDiff supplies evidence; RDE interprets it under a TaskContract and policies. |
| **Policy engine** | Policy consumes `RDEResult`; RDE does not choose organizational outcomes by itself. |
| **Safety filter / content moderation** | Broader safety systems may wrap RDE; RDE classifies deviation types for audit and gating, not universal harm blocking. |
| **LLM-as-judge** | Optional LLM-assisted semantic modes may exist; default paths are structural and rule-based. RDE is not reducible to an LLM evaluator. |

## 5. RDE classification taxonomy

Canonical string literals (JSON and Python) for **`RDEClassification`**:

| Value | Informal reading |
|-------|------------------|
| `preserved` | No substantial deviation detected under the contract and evidence. |
| `authorized_deviation` | Change aligns with allowed ΔM / contract constraints. |
| `benign_incidental_drift` | Minor drift not matching “preserved” but treated as low concern under policy. |
| `suspicious_drift` | Potentially unauthorized or fragile change warranting review or revision. |
| `critical_corruption` | Severe structural or contractual violation; typically blocks automatic application. |
| `creative_deviation` | Intentional creative change under creative-mode contracts when classified as such. |

Design documents may use phrases such as “inferred extension” or “critical distortion”; map them to **`creative_deviation`** / **`critical_corruption`** respectively when bridging prose to this implementation vocabulary.

## 6. Evidence and evaluation kind

- **`RdeEvaluationKind`**: `pre_synthetic` (e.g. execution gate before structural diff) vs `post_structural` (full structural evaluation).
- **`EvidenceBasis`**: enumerates sources such as `structural_diff`, `semantic_delta`, `tool_risk_rule`, `execution_contract`, etc. RDE results should record which bases contributed.

Classifications must be **traceable** to declared evidence types, not only to generator narrative.

## 7. Policy boundary

- **RDE** assigns **`RDEClassification`**, risk, and an advisory **`required_action`** on `RDEResult`.
- **Policy** (`PolicyDecision`) selects operational actions (`approve`, `halt`, `rollback`, …) consistent with `ReviewPolicy`, runtime posture, and optional institution rules.

Mixing policy outcomes into RDE classification fields is a **layering violation**.

## 8. Non-claims and scope limits

This specification does **not** assert:

- **Semantic equivalence** of natural language or code beyond what structural/stub/optional-LLM pipelines implement.
- **Production-grade identity, cryptographic audit, or legal compliance**; those belong to deployment and institution layers.
- **Statistical external validity** of scores outside documented benchmarks and fixtures.

For operational compatibility expectations of serialized artefacts, see `docs/51_openayane_rde_release_compatibility_policy.md`.

## 9. RDE differential review (change governance)

When modifying RDE behaviour or fixtures, reviewers should classify the change along these axes (consistent with project Phase 5/6 governance):

| Axis | Question |
|------|----------|
| **Preserved elements** | Does the change keep stable identifiers, classification vocabulary, and audit action enums unless intentionally versioned? |
| **Authorized transformations** | Are contract semantics (`TaskContract`, `ReviewPolicy`) updated in a documented, migration-aware way? |
| **Inferred extensions** | Are new classifications, evidence bases, or optional fields explicitly additive and schema-documented? |
| **Suspicious drift risk** | Could the change silently alter outcomes for the same inputs (semantic RDE / policy bugfix vs regression)? |
| **Critical distortion risk** | Could the change hide halt/rollback or audit completeness? |

## 10. References

- Implementation models: `src/openayane_rde/core/models.py`
- JSON exchange schemas: `schemas/*.schema.json`
- Schema prose: `specs/task_contract_schema.md`, `specs/rde_result_schema.md`, `specs/audit_event_schema.md`, `specs/relation_store_schema.md`
- Basic design (Japanese): `docs/02_openayane_basic_design.md`
