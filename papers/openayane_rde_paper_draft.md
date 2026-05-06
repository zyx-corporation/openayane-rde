---
title: "OpenAyane RDE — Technical report draft (skeleton)"
version: "0.1-draft"
status: "skeleton"
date: "2026-05-06"
---

# Meaning-change auditing with the Resonant Deviation Evaluator (RDE): a technical sketch

## Keywords

semantic drift; structural diff; task contracts; policy separation; auditability; generative systems

## Abstract

**(Skeleton — replace with empirical abstract.)**  
We outline OpenAyane RDE, a mechanism that evaluates **meaning-relevant change (ΔM)** between a baseline artifact and a generator-produced successor under an explicit **TaskContract**. RDE separates **classification of deviation** from **policy decisions** and **institutional accountability**, grounding decisions in structural evidence and optional semantic estimates rather than generator self-narrative alone. This draft references the public specification, schema prose, and a small Phase 6 benchmark baseline; it does **not** yet report user studies or large-corpus evaluations.

## 1. Introduction

- Motivation: silent semantic drift in LLM and agent outputs.
- Gap: diff tools and LLM-as-judge setups that collapse evaluation and policy.
- Contribution sketch: contract-centred evaluation, RDE classification vocabulary, audit/relation hooks (see implementation repository).

## 2. Related work

**(Skeleton.)** Diff tools, ML safety evaluation, provenance, program analysis, document QA. *Citations TBD.*

## 3. Architecture

High-level data flow (expand with diagram in camera-ready version):

1. **TaskContract** — allowed/forbidden ΔM descriptions, protected element kinds, review hooks.
2. **GeneratorOutput** — payload + **SelfReport** (non-authoritative).
3. **StructuralDiff** — Markdown / JSON / Python AST (extensible).
4. **SemanticDelta** — structural-baseline / stub modes in current release.
5. **RDEResult** — `RDEClassification`, risk, evidence basis.
6. **PolicyDecision** — operational action; must not subsume RDE labels.
7. **AuditEvent** / relation updates — history for feedback loops.

**Normative terms:** `specs/rde_core_spec.md`  
**Serialized shapes:** `specs/task_contract_schema.md`, `specs/rde_result_schema.md`, `specs/audit_event_schema.md`, `specs/relation_store_schema.md`

## 4. Evaluation (repository evidence)

- **Benchmark tree:** `benchmarks/README.md`
- **Harness:** `benchmarks/evaluate.py`, definitions in `benchmarks/METRICS.md`
- **Baseline note:** `reports/phase6_baseline_evaluation.md` and `reports/phase6_baseline_eval.json`
- **Regression:** `tests/golden/`, `tests/benchmarks/`

**(Skeleton.)** Future versions should add: larger corpora, locale coverage, human-review studies, calibration analysis — only where claims are explicitly scoped.

## 5. Limitations and non-claims

See **`specs/known_limitations.md`** (high assurance, semantic equivalence, production identity, benchmark scope, external validity).

## 6. Ethics, dual use, and conflicts of interest

**(Placeholder.)** Discuss misuse risks of automated drift detection (e.g. over-trusting automation, false negatives). Declare funding, employer, and model-provider COI for any camera-ready version.

## 7. Reproducibility

- Repository: OpenAyane RDE (implementation plan and Phase 6 artefacts in-tree).
- **Recorded implementation snapshot** for the Phase 6 baseline JSON: see `git_commit` in `reports/phase6_baseline_eval.json`.

## 8. References

**(Skeleton.)** Add bibliographic entries when promoting beyond internal draft.

- OpenAyane RDE specs: `specs/`
- Phase 6 plan: `docs/60_openayane_rde_phase6_issue_branch_plan.md`
- Phase 6 completion (process record): `docs/62_openayane_rde_phase6_completion_report.md`
