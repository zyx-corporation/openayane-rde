---
title: "OpenAyane RDE Phase 6 Research Evaluation and Public Specification"
version: "0.1"
date: "2026-05-05"
status: "draft-specification"
---

# OpenAyane RDE Phase 6 Research Evaluation and Public Specification

## 0. Purpose

Phase 6 establishes OpenAyane RDE as a reproducible research target and a publishable technical specification.

Phase 6 does not redefine the operational boundaries fixed by Phase 5. It formalizes evaluation methodology, public schemas, benchmark reproducibility, and publication artifacts.

```text
Phase 5:
  operational invocation, integration, observability, regression, release discipline

Phase 6:
  reproducible evaluation protocol, public specification set, benchmark governance, paper/report artifacts
```

The core question changes from:

```text
Can OpenAyane be used safely and reproducibly in bounded operations?
```

to:

```text
Can OpenAyane's meaning-change governance be measured, reproduced, and communicated as a research-grade specification?
```

## 1. Normative references

Read this document together with:

```text
- docs/00_development_plan.md
- docs/60_openayane_rde_phase6_issue_branch_plan.md
- docs/50_openayane_rde_phase5_operational_hardening_spec.md
- docs/51_openayane_rde_release_compatibility_policy.md
- docs/52_openayane_rde_phase5_completion_report.md
```

Phase 6 depends on the operational baseline of Phase 5 and inherits its non-goals regarding production assurance, cryptographic guarantees, and legal/compliance judgement.

## 2. Scope

### 2.1 In scope

```text
- public-facing core specification of RDE evaluation semantics
- publishable schema set for TaskContract / RDEResult / AuditEvent / RelationStore
- benchmark suite curation and reproducibility protocol
- metric definitions and evaluation scripts for repeatable scoring
- baseline experiment matrix and result report templates
- limitation registry (known failure modes and unresolved problems)
- paper/report draft for external communication
```

### 2.2 Out of scope

```text
- production SLA claims
- cryptographic audit chain implementation
- formal legal/compliance certification
- unrestricted autonomous execution rollout
- replacing operational policy with benchmark score optimization
```

## 3. Phase 6 maturity target

Phase 6 targets **Research Evaluation Ready**, not production certification.

```text
Research Evaluation Ready:
  public artifacts are sufficient for third parties to re-run benchmark fixtures,
  validate schema contracts, and interpret metric outputs under documented assumptions.

Not claimed:
  high-assurance security certification, legal validity, or universal domain generalization.
```

## 4. Architectural principle

Phase 6 preserves existing layer boundaries:

```text
RDE:
  classifies meaning-change signals

Policy:
  maps classification to actions

Runtime:
  bounded execution path

Institution Bridge:
  authority and accountability routing

Phase 6:
  externalizes definitions, metrics, fixtures, and limitations for reproducible evaluation
```

Phase 6 must not collapse RDE semantics into a single benchmark score. Benchmark outputs are observational evidence, not authority replacement.

## 5. Deliverable groups

Recommended issue groups (aligned with `docs/60_openayane_rde_phase6_issue_branch_plan.md`):

```text
P6-1: RDE Core Public Specification
P6-2: Public Schema Bundle and Version Policy
P6-3: Benchmark Fixture Catalog and Metadata
P6-4: Structural Benchmark Fixtures (Markdown / JSON / Python)
P6-5: Long-chain and Self-report Mismatch Benchmarks
P6-6: Evaluation Runner and Metrics Pipeline
P6-7: Baseline Experiments and Result Pack
P6-8: Paper / Technical Report Draft
P6-9: Known-Limitations and Threats-to-Validity Registry
P6-10: Phase 6 completion report
```

## 6. Public specification set

### 6.1 Required public specs

```text
specs/rde_core_spec.md
specs/task_contract_schema.md
specs/audit_event_schema.md
specs/relation_store_schema.md
specs/benchmark_protocol.md
```

### 6.2 Specification requirements

```text
- normative vs informative sections clearly separated
- glossary for core terms (delta_m, protected_elements, drift_pattern)
- compatibility notes for schema evolution
- explicit unsupported cases and assumptions
- traceability from metrics to source events
```

## 7. Benchmark suite requirements

### 7.1 Benchmark domains

```text
benchmarks/markdown_drift/
benchmarks/json_schema_corruption/
benchmarks/python_api_drift/
benchmarks/long_chain_document_corruption/
benchmarks/generator_self_report_mismatch/
```

### 7.2 Fixture metadata

Each fixture should provide:

```text
- fixture_id
- source domain and provenance note
- intended risk class
- expected RDE label(s)
- protected element expectation
- known ambiguity notes
```

### 7.3 Governance rule

Any fixture update that changes expected labels must include a rationale note and be recorded as a benchmark-drift change.

## 8. Metric definition

### 8.1 Primary metrics

```text
- unauthorized_change_detection_rate
- critical_corruption_recall
- suspicious_drift_precision
- false_positive_rate
- self_report_mismatch_detection_rate
- long_chain_drift_detection_rate
- audit_completeness_rate
- latency_ms_p50
- latency_ms_p95
```

### 8.2 Secondary metrics

```text
- human_review_rate
- human_review_reduction_rate (relative to baseline policy profile)
- rollback_success_rate
- relation_trust_calibration_correlation
```

### 8.3 Reporting requirement

Results must be emitted in machine-readable JSON and a human-readable markdown report:

```text
.openayane/reports/research_eval_YYYYMMDD.json
.openayane/reports/research_eval_YYYYMMDD.md
```

## 9. Reproducibility protocol

### 9.1 Environment pinning

```text
- Python version and dependency lock reference
- OS/runtime assumptions
- deterministic seed policy where applicable
- benchmark data version stamp
```

### 9.2 Execution contract

```text
- one command to run benchmark matrix
- one command to validate schemas and fixtures
- one command to generate publication-ready summary tables
```

### 9.3 Acceptance criteria

```text
- fresh clone can reproduce baseline metrics with documented tolerances
- failed reproducibility returns actionable diagnostics
- generated reports include commit hash / config profile / fixture version
```

## 10. Baseline experiment matrix

Baseline runs should include:

```text
dimensions:
  - domain (markdown/json/python/long-chain/mismatch)
  - policy profile (strict/default/permissive)
  - relation store backend (json/sqlite where supported)
  - execution mode (local deterministic path)
```

The matrix should define minimum sample counts and confidence notes for each metric.

## 11. Known limitations and validity threats

Phase 6 must maintain a living registry:

```text
docs/61_openayane_rde_phase6_limitations_registry.md
```

Minimum categories:

```text
- external validity limits
- benchmark selection bias
- schema/fixture representativeness limits
- unresolved semantic ambiguity classes
- latency measurements not representative of remote/LLM-heavy paths
```

## 12. Publication artifacts

### 12.1 Required artifact

```text
papers/openayane_rde_paper_draft.md
```

### 12.2 Minimum structure

```text
- problem statement
- RDE architecture summary
- benchmark protocol
- experimental results
- ablation or comparative notes
- limitations and future work
```

## 13. Security and safety posture

Phase 6 does not alter the safety baseline from Phase 5.

Required explicit statements:

```text
- benchmark success does not imply production safety certification
- no cryptographic tamper-proof guarantee is newly introduced by Phase 6 docs
- no legal/compliance guarantee is introduced by benchmark publication
- external side effects remain opt-in and auditable
```

## 14. Recommended Phase 6 Issues

```text
P6-1: Publish RDE core specification draft
P6-2: Publish TaskContract / AuditEvent / RelationStore schema documents
P6-3: Add benchmark fixture metadata and validation rules
P6-4: Add Markdown / JSON / Python structural benchmark fixtures
P6-5: Add long-chain drift and self-report mismatch benchmarks
P6-6: Add research evaluation runner and metric aggregator
P6-7: Produce baseline result pack and reference reports
P6-8: Draft paper/technical report for external review
P6-9: Create limitations registry and validity-threat taxonomy
P6-10: Add Phase 6 completion report
```

## 15. Acceptance criteria for Phase 6 exit

Phase 6 can be considered Research Evaluation Ready when:

```text
- public core specs exist and are internally consistent
- schema documents are aligned with implemented models
- benchmark fixtures are reproducible with metadata and expected labels
- metric pipeline outputs stable reports with traceable provenance
- baseline result pack is generated and archived
- known limitations are documented and linked from the main report
- publication draft exists and reflects actual measured outcomes
```

## 16. RDE differential review

### 16.1 Preserved elements

Phase 6 preserves the separation between RDE semantics and operational policy actions, and keeps institutional accountability outside of benchmark score logic.

### 16.2 Authorized transformations

Operational artifacts from Phase 5 are transformed into public, reproducible research artifacts and benchmark protocols.

### 16.3 Inferred extensions

```text
- benchmark protocol specification
- reproducibility report format
- limitations registry
- publication draft pipeline
```

### 16.4 Unresolved elements

```text
- cross-domain generalization beyond current fixture families
- adversarial prompt robustness under remote model variability
- formal proof obligations for classification guarantees
```

### 16.5 Drift risks

```text
- benchmark optimization distorts real operational safety priorities
- schema publication drifts from implementation without version controls
- fixture labels become stale but remain trusted as canonical truth
- paper claims exceed measured evidence bounds
```

## 17. Final statement

Phase 6 converts OpenAyane RDE from an operationally usable system into a reproducible research object.

It should improve interpretability, comparability, and external scrutiny of RDE behavior.

It must not overstate certainty, erase boundary assumptions, or substitute benchmark performance for accountable governance.

## 18. Revision history

| Version | Date | Notes |
|---|---|---|
| 0.1 | 2026-05-05 | Initial Phase 6 research evaluation and public specification draft. |
