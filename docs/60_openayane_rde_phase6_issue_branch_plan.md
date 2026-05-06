---
title: "OpenAyane RDE Phase 6 Issue Branch and Execution Plan"
version: "0.1"
date: "2026-05-05"
status: "draft-plan"
---

# OpenAyane RDE Phase 6 Issue Branch and Execution Plan

## 0. Purpose

This document defines the Phase 6 issue decomposition, recommended branch names, and execution order.

Phase 6 is defined in `docs/00_development_plan.md` as **Research Evaluation and Public Specification**. It follows Phase 5, whose completion report fixes the repository at **Operational Pilot Ready**.

Phase 6 should not primarily add new execution capability. It should transform the implemented OpenAyane RDE stack into reproducible research artefacts, public specifications, benchmark fixtures, and technical-report material.

## 1. Phase 6 boundary

Phase 6 asks:

```text
Can the implemented RDE mechanism be described, evaluated, reproduced, and criticized as a public research/specification artefact?
```

It does not ask:

```text
Can OpenAyane run autonomously in production?
```

That distinction is essential. Phase 6 is a research/specification phase, not a capability escalation phase.

## 2. Required outputs from development plan

`docs/00_development_plan.md` lists Phase 6 target artefacts such as:

```text
specs/rde_core_spec.md
specs/task_contract_schema.md
specs/audit_event_schema.md
specs/relation_store_schema.md
benchmarks/
  markdown_drift/
  json_schema_corruption/
  python_api_drift/
  long_chain_document_corruption/
  generator_self_report_mismatch/
papers/
  openayane_rde_paper_draft.md
```

It also lists evaluation metrics such as:

```text
Unauthorized change detection rate
Critical corruption recall
Suspicious drift precision
False positive rate
Human review reduction rate
Rollback success rate
Long-chain drift detection rate
Self-report mismatch detection rate
Relation trust calibration correlation
Latency p50 / p95
Audit completeness
```

## 3. Recommended Phase 6 Issues

The following issues should be created for Phase 6.

| P6 | Purpose | Completion type target |
|---|---|---|
| P6-1 | Define public RDE Core specification | `documentation / public spec` |
| P6-2 | Publish TaskContract / RDEResult / AuditEvent schema specs | `documentation / schema spec` |
| P6-3 | Define benchmark fixture structure | `implementation / benchmark skeleton` |
| P6-4 | Add markdown / JSON / Python corruption benchmark fixtures | `implementation / benchmark fixtures` |
| P6-5 | Add long-chain drift and self-report mismatch benchmarks | `implementation / benchmark fixtures` |
| P6-6 | Define evaluation metrics and scoring scripts | `implementation / evaluation harness` |
| P6-7 | Generate baseline evaluation report from current implementation | `documentation / evaluation report` |
| P6-8 | Draft public technical report / paper skeleton | `documentation / paper draft` |
| P6-9 | Document known limitations and non-claims | `documentation / limitations spec` |
| P6-10 | Add Phase 6 completion report | `documentation / completion record` |

## 4. Recommended execution order and branches

Phase 6 should use **one Issue = one branch = one PR** by default.

Recommended execution order:

| Order | Issue | Purpose | Branch | Rationale |
|---:|---|---|---|---|
| 1 | P6-1 | RDE Core public specification | `phase6/p6-1-rde-core-spec` | The core public terms must be fixed before schema and benchmark documents depend on them. |
| 2 | P6-2 | TaskContract / RDEResult / AuditEvent schema specs | `phase6/p6-2-schema-specs` | Public schemas should follow the core specification vocabulary. |
| 3 | P6-3 | Benchmark fixture structure | `phase6/p6-3-benchmark-skeleton` | Benchmark directory layout should exist before individual fixtures are added. |
| 4 | P6-4 | Markdown / JSON / Python corruption fixtures | `phase6/p6-4-structural-benchmark-fixtures` | Structural corruption fixtures are the lowest-risk benchmark base. |
| 5 | P6-5 | Long-chain drift and self-report mismatch benchmarks | `phase6/p6-5-long-chain-self-report-benchmarks` | These depend on baseline fixture conventions from P6-3/P6-4. |
| 6 | P6-6 | Evaluation metrics and scoring scripts | `phase6/p6-6-evaluation-metrics-harness` | Metrics should score already-defined benchmark structures. |
| 7 | P6-7 | Baseline evaluation report | `phase6/p6-7-baseline-evaluation-report` | Report should be generated from fixtures and scoring scripts. |
| 8 | P6-9 | Known limitations and non-claims | `phase6/p6-9-limitations-nonclaims` | Limitations should reflect actual benchmark/report findings. |
| 9 | P6-8 | Public technical report / paper skeleton | `phase6/p6-8-public-technical-report` | Paper skeleton should cite specs, benchmarks, metrics, and limitations. |
| 10 | P6-10 | Phase 6 completion report | `phase6/p6-10-completion-report` | Exit record comes last. |

P6-8 is intentionally after P6-9. The public report should not overclaim before the limitations document exists.

## 5. Issue detail drafts

### 5.1 P6-1: Define public RDE Core specification

Scope:

```text
- define RDE as meaning-change audit layer
- define ΔM, TaskContract, StructuralDiff, SemanticDelta, RDEResult, PolicyDecision, AuditEvent
- state what RDE is not: Diff, Policy, Safety Filter, LLM Evaluator
- state preserved / authorized transformation / inferred extension / suspicious drift / critical distortion categories
```

Acceptance criteria:

```text
- `specs/rde_core_spec.md` exists
- terms align with implemented model names where applicable
- non-claims are explicit
- RDE differential review is included
```

### 5.2 P6-2: Publish schema specs

Scope:

```text
- `specs/task_contract_schema.md`
- `specs/rde_result_schema.md`
- `specs/audit_event_schema.md`
- `specs/relation_store_schema.md`
- references to JSON schemas under `schemas/` where they exist
```

Acceptance criteria:

```text
- schema docs exist
- required / optional fields are distinguished
- breaking-change policy references docs/51
- examples are included
```

### 5.3 P6-3: Define benchmark fixture structure

Scope:

```text
benchmarks/
  README.md
  markdown_drift/
  json_schema_corruption/
  python_api_drift/
  long_chain_document_corruption/
  generator_self_report_mismatch/
```

Acceptance criteria:

```text
- directory skeleton exists
- fixture naming convention exists
- expected-output convention exists
- benchmark non-goals are stated
```

### 5.4 P6-4: Add structural benchmark fixtures

Scope:

```text
- markdown heading deletion / citation deletion / number change
- JSON required key deletion / type change
- Python function signature change / public API deletion / exception handling removal
```

Acceptance criteria:

```text
- at least one fixture per domain
- expected RDE classification documented
- golden/regression command can include or ignore fixtures explicitly
```

### 5.5 P6-5: Add long-chain and self-report mismatch benchmarks

Scope:

```text
- long-chain document drift fixture series
- generator self_report mismatch fixture
- audit completeness fixture where applicable
```

Acceptance criteria:

```text
- at least one long-chain fixture sequence
- at least one self-report mismatch fixture
- expected drift pattern described
```

### 5.6 P6-6: Define evaluation metrics and scoring scripts

Scope:

```text
- metric definitions
- scoring script skeleton
- output JSON report shape
- mapping from benchmark expected labels to metrics
```

Acceptance criteria:

```text
- `benchmarks/evaluate.py` or equivalent exists
- metrics definitions documented
- script produces machine-readable report
- no claims of statistical validity beyond fixture scope
```

### 5.7 P6-7: Generate baseline evaluation report

Scope:

```text
- run current implementation on benchmark fixtures
- produce `reports/phase6_baseline_evaluation.md` or equivalent
- include latency if available from Phase 5 perf harness
```

Acceptance criteria:

```text
- baseline report exists
- report names implementation version/commit
- failures and gaps are included rather than hidden
```

### 5.8 P6-8: Draft public technical report / paper skeleton

Scope:

```text
papers/openayane_rde_paper_draft.md
```

Acceptance criteria:

```text
- title / abstract / keywords exist
- architecture and evaluation sections are scaffolded
- references to specs and benchmark reports exist
- COI / limitations placeholder exists
```

### 5.9 P6-9: Document known limitations and non-claims

Scope:

```text
specs/known_limitations.md
```

Acceptance criteria:

```text
- high assurance non-claim
- semantic equivalence non-claim
- production identity non-claim
- benchmark scope limitations
- external validity limitations
```

### 5.10 P6-10: Add Phase 6 completion report

Scope:

```text
docs/62_openayane_rde_phase6_completion_report.md
```

Acceptance criteria:

```text
- Issue/PR table
- produced artefact table
- benchmark/evaluation summary
- open limitations
- Phase 7 or publication handoff, if any
```

## 6. PR metadata rule

Every Phase 6 PR should include:

```text
Primary issue: #NN
Completion type:
RDE Notes:
Test plan:
Non-claims preserved:
```

For benchmark or evaluation PRs, also include:

```text
Benchmark scope:
Expected classification changes:
Known limitations:
```

## 7. Branching exception policy

Avoid combining Phase 6 issues unless the PR is documentation-only and the primary/secondary issue relationship is explicit.

Allowed early combined branch only if necessary:

```text
phase6/issues-p6-1-p6-2-core-and-schema-specs
```

Even then, prefer separate branches because public specification and schema documentation change different kinds of meaning.

## 8. RDE differential review

### 8.1 Preserved elements

This plan preserves the Phase 6 goal from `docs/00_development_plan.md`: research evaluation and public specification, not production capability escalation.

### 8.2 Authorized transformations

The Phase 6 concept is transformed into issue-sized work packages, branch names, acceptance criteria, and PR metadata requirements.

### 8.3 Inferred extensions

This plan introduces explicit P6 numbering and branch names. These are project-management artefacts, not theoretical changes to RDE.

### 8.4 Resolved delivery (PR stack, no Phase 6 issues)

Work landed on `main` via stacked PRs (May 2026); dedicated GitHub Issues were optional and not created for every P6 row.

| P6 slice | PR |
|---------|-----|
| P6-1 / P6-2 | [#84](https://github.com/zyx-corporation/openayane-rde/pull/84) |
| P6-3 | [#91](https://github.com/zyx-corporation/openayane-rde/pull/91) |
| P6-4 | [#86](https://github.com/zyx-corporation/openayane-rde/pull/86) |
| P6-5 | [#87](https://github.com/zyx-corporation/openayane-rde/pull/87) |
| P6-6 | [#88](https://github.com/zyx-corporation/openayane-rde/pull/88) |
| P6-7 | [#89](https://github.com/zyx-corporation/openayane-rde/pull/89) |
| P6-9 / P6-8 / P6-10 | [#90](https://github.com/zyx-corporation/openayane-rde/pull/90) |

See also `docs/62_openayane_rde_phase6_completion_report.md` §2. **Stack tip:** avoid `gh pr merge --delete-branch` on a base branch while child PRs are still open, or child PRs may auto-close.

### 8.5 Drift risks

Key risks:

```text
- Phase 6 becomes feature development instead of research/specification
- benchmark fixtures overfit to existing implementation
- baseline report hides failures
- paper draft overclaims external validity
- schema docs drift from Pydantic / JSON schemas
```

### 8.6 Next update policy

If Phase 6 work is later re-split into GitHub Issues, add an **Issue** column or table alongside the PR table in §8.4. PR links above remain the historical merge record.

## 9. Final statement

Phase 6 should make OpenAyane RDE legible, reproducible, and criticizable.

It should not make OpenAyane appear more complete, more general, or more production-ready than the implemented evidence supports.
