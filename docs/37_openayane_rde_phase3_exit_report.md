---
title: "OpenAyane RDE Phase 3 Exit Report"
version: "0.1"
date: "2026-05-05"
status: "exit-fixed"
---

# OpenAyane RDE Phase 3 Exit Report

## 0. Purpose

This document fixes the Phase 3 exit boundary for OpenAyane RDE.

Phase 3 is not declared production-ready. It is declared **L1 internal-pilot ready with L1+ hardening**. The purpose of this report is to make that distinction explicit before starting Phase 4 specification work.

This document also records which parts of Phase 3 are implementation-complete, which parts are design or planning complete, and which concerns are intentionally carried into Phase 4 or later L2/L3 hardening.

## 1. Exit statement

```text
Phase 3 exit status: accepted for Phase 4 specification
Maturity: L1 internal-pilot ready + L1+ hardening
Production status: not production-ready
Phase 4 permission: proceed with specification and interface skeletons
Phase 4 restriction: do not treat Phase 3 as high-assurance runtime infrastructure
```

Phase 3 may be used as a basis for Phase 4 design because the following loop is now implemented:

```text
ToolCallRequest
  -> ExecutionTaskContract
  -> ToolCallRisk / policy pre-check
  -> ExecutionGateDecision
  -> SafeExecutionRuntime or HumanReviewWorkflow
  -> AuditLog / SQLiteRelationStore linkage
  -> optional post-execution RDE path
```

This is sufficient for designing the institutional bridge. It is not sufficient for unrestricted production execution.

## 2. Included implementation scope

Phase 3 includes the following merged implementation scope.

```text
- Agent Execution Gate
- Tool call contract construction
- Tool side-effect taxonomy
- Policy denylist and network host allowlist pre-checks
- SafeExecutionRuntime with bounded local file actions
- allowlisted subprocess execution
- subprocess timeout / cancellation handling
- HumanReviewWorkflow
- SQLiteRelationStore
- rollback plan / rollback result core
- rollback audit helpers and recovery playbook
- optional semantic evaluator seam
- PostExecutionDiff -> Phase 1 RDE connector
- AuditLog helper functions and JSONL append path
- RDEResult.evaluation_kind
- RDEResult.evidence_basis
- completion-marker PR for Issues #17-#23
```

The completion-marker PR exists only as an audit marker. It does not introduce code changes.

## 3. Completion type table

The following table fixes the completion interpretation for closed Phase 3 issues. This prevents Done from being read as a single undifferentiated state.

| Issue | Area | Completion type | Exit interpretation |
|---|---|---|---|
| #2 | evidence_basis | implementation | Evaluation kind and evidence basis are machine-readable. |
| #3 | Phase3ExecutionEvaluationResult | design-decision | Dedicated aggregate model is not introduced yet. Revisit if UI/API needs a single execution-to-RDE view. |
| #4 | max_runtime_ms | implementation | Subprocess timeout path is implemented. Not a full resource sandbox. |
| #5 | subprocess allowlist | implementation | Subprocess execution is disabled by default and allowlist-gated. |
| #6 | external_side_effect_kind | implementation | External side effects are typed beyond network_allowed. |
| #7 | SQLite v2 migration | design-note / migration plan | v2 plan exists; migration implementation remains future work. |
| #8 | Project board | ops / project-governance | Board governance is operational metadata, not code implementation. |
| #9 | Human Review Workflow | implementation | Workflow core exists; authority/identity layer remains Phase 4+. |
| #10 | SQLiteRelationStore | implementation | SQLite backend exists; not final graph/vector relation memory. |
| #11 | Agent Execution Gate | implementation | Gate model and decision flow exist. |
| #12 | Safe Execution Runtime | implementation | Application-level bounded runtime exists. Not OS sandbox. |
| #13 | Tool Call Gating | implementation | Tool gate core exists. |
| #14 | Rollback Manager | implementation / MVP rollback scope | Local file snapshot rollback exists. External/transactional rollback remains future work. |
| #15 | Optional Semantic Evaluator | implementation / optional evaluator MVP | Evaluator seam exists; it remains subordinate to structural governance. |
| #17 | Human Review hardening | implementation / authorized transformation | Critical defaults to halt; human review is available by explicit policy configuration. |
| #18 | SQLite backend migration path | implementation | JSON-to-SQLite import and rollback-safe notes exist. Distinct from v2 schema migration. |
| #19 | Tool side-effect gate | implementation / L1+ hardening | Denylist, network host allowlist, and gate audit linkage exist. |
| #20 | Safe runtime hardening | implementation / L1+ hardening | Cancellation and subprocess polling hardening are included. |
| #21 | Policy bridge | implementation / L1+ hardening | Relation history can influence execution gate rationale. |
| #22 | Rollback audit | implementation / L1+ hardening | Rollback audit and recovery playbook are included. |
| #23 | Semantic evaluator seam | implementation / L1+ hardening | Optional evaluator integration seam and exports are included. |

## 4. Achieved L1 criteria

Phase 3 satisfies the internal-pilot criteria below.

| Criterion | Status | Notes |
|---|---|---|
| Gate / runtime / review traceability | achieved for core paths | Audit helpers and integration tests exist. Some entrypoints may still require explicit audit_log_path wiring. |
| PostExecutionDiff to RDE path | achieved | `run_phase1_evaluation_from_post_execution_diff` connects execution output to Phase 1 evaluation. |
| Synthetic vs structural distinction | achieved | `evaluation_kind` and `evidence_basis` prevent synthetic gate results from being mistaken for structural RDE. |
| Path traversal / symlink tests | achieved minimally | Basic regression tests exist; TOCTOU / file descriptor race remains future hardening. |
| Human review to runtime resume | achieved | `approve` and `approve_dry_run` paths exist. |
| CI signal | achieved for recent PR marker | PR #24 CI succeeded before merge. Main workflow should continue to be monitored after future commits. |

## 5. Not achieved L2 criteria

Phase 3 does not yet satisfy the following L2 / bounded-production criteria.

```text
- HTTP client execution via explicit proxy and URL/method/redirect policy
- SQLite schema v2 migration implementation for complete review payload persistence
- write queue or RelationStore service for multi-agent / concurrent writer operation
- full rollback E2E for multi-file delete and git reverse patch
- OS-level sandbox or container isolation
- cryptographic audit log
- reviewer authority / InstitutionRule / PoP-UID integration
- complete UI for human review and evidence inspection
```

These are not failures of Phase 3. They are explicitly carried forward.

## 6. Phase 4 readiness decision

Phase 4 may begin under the following constraint.

```text
Allowed:
- Phase 4 specification
- boundary models and interfaces
- InstitutionRule schema skeleton
- authority / reviewer identity reference models
- provenance schema extension
- policy halt vs RDE halt distinction
- evidence handoff from Phase 3 to Phase 4

Not allowed yet:
- claiming Phase 3 is production-ready
- treating policy halt as semantic RDE halt
- treating rollback plan existence as actual reversibility
- using optional semantic evaluator output as a substitute for structural governance
- depending on SQLite v2 migration as already implemented
```

## 7. Phase 4 carry-over requirements

Phase 4 must explicitly consume the following Phase 3 outputs.

```text
- ExecutionGateDecision
- ExecutionTaskContract
- ToolCallRisk
- RDEResult.evaluation_kind
- RDEResult.evidence_basis
- AuditEvent.event_id
- ToolExecutionResult.audit_event_id
- ReviewRequest / ReviewDecision
- RollbackPlan / RollbackResult
- RelationContext
- policy_adjustment_notes / gating rationale where available
```

Phase 4 must not redefine these as final institutional truth. It should treat them as evidence inputs.

## 8. RDE differential review

### 8.1 Preserved elements

Phase 3 preserves the original OpenAyane intent that evaluation, policy, execution, review, rollback, and audit are separate responsibilities. It also preserves the RDE distinction between meaning-change evaluation and execution governance.

### 8.2 Authorized transformations

The abstract governance layer was transformed into concrete Python models, SQLite persistence, audit helpers, runtime checks, and human review workflow. This is an authorized implementation transformation.

### 8.3 Inferred extensions

The following extensions were inferred during implementation.

```text
- evidence_basis
- external_side_effect_kind
- denied_tool_names
- network_hosts_allowlist
- cancellation_event
- policy_adjustment_notes / gating rationale
- optional semantic integration seam
- rollback recovery playbook
```

These are consistent with the RDE design direction.

### 8.4 Unresolved elements

The following elements remain unresolved.

```text
- Institution authority model
- reviewer authorization
- SQLite v2 migration implementation
- HTTP proxy and network execution policy
- high-assurance sandbox
- cryptographic audit
- UI-level evidence review
```

### 8.5 Drift risks

Key drift risks are:

```text
- Done being read as production-ready
- policy halt being read as RDE semantic halt
- synthetic RDE being read as structural RDE
- rollback metadata being read as actual reversibility
- optional semantic evaluator being promoted into a decision authority
- Phase 4 institution layer masking unresolved runtime assumptions
```

### 8.6 Next update policy

Before Phase 4 implementation grows beyond skeletons, create or update issues for:

```text
- SQLite v2 migration implementation
- Phase 4 InstitutionRule model
- AuthorityRef / ReviewerAuthority model
- policy halt vs RDE halt payload distinction
- evidence handoff schema
- HTTP proxy and URL policy
```

## 9. Final exit declaration

```text
Phase 3 is closed as L1 internal-pilot ready with L1+ hardening.
Phase 3 is not closed as L2 bounded-production ready.
Phase 4 may start with specification and interface skeleton work.
```
