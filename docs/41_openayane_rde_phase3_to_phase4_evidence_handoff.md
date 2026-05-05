---
title: "OpenAyane RDE Phase 3 → Phase 4 Evidence Handoff Requirements"
version: "0.1"
date: "2026-05-05"
status: "design-note"
---

# OpenAyane RDE Phase 3 → Phase 4 Evidence Handoff Requirements

## 0. Purpose and normative references

This design note makes **Phase 3 → Phase 4 evidence handoff** explicit so Institution Bridge work does not rely on implicit context. It supports auditability and RDE-style review of documentation changes.

**Normative references (read together):**

- `docs/37_openayane_rde_phase3_exit_report.md` — what Phase 3 exit guarantees and what remains out of scope.
- `docs/40_openayane_rde_phase4_institution_bridge_spec.md` — Phase 4 scope, `EvidenceHandoff` / `InstitutionalDecision` / `HaltProvenance` intent.

**Non-goals of this handoff path**

- It is **not** cryptographic proof of authority, PoP-UID, or production identity.
- It is **not** a license to treat Phase 3 outputs as final institutional truth; they remain **evidence inputs** to Phase 4.

The implemented Pydantic shapes live under `openayane_rde.institution`; this document specifies **what must be present or explicitly absent** when constructing bridge records, independent of any UI or persistence.

---

## 1. Design principle

```text
Phase 4 consumes Phase 3 artefacts as evidence.
Phase 4 must not silently upgrade missing evidence into inferred authority, reversibility, or approval.
```

**RDE differential review:** When changing this document or handoff behaviour, use the checklist in `docs/01_project_management_ja.md` §7 (preserved / authorized transformation / inferred extension / drift risk). Documentation changes are still **meaning changes** for governance.

---

## 2. Phase 3 evidence inventory

Phase 4 bridge design assumes the following **Phase 3 types** may appear in the evidence chain (see also §3 of `docs/40_openayane_rde_phase4_institution_bridge_spec.md`):

| Phase 3 artefact | Role in handoff |
|---|---|
| `ExecutionTaskContract` | Contract identity and obligation context (`contract_id`). |
| Tool call / gate context | `tool_call_id`, gate linkage. |
| `ToolCallRisk` | Risk context for rule and authority matching. |
| `ExecutionGateDecision` | Gate outcome and rationale IDs where emitted. |
| `ToolExecutionResult` | Execution outcome; linkage via audit fields. |
| `ReviewRequest` / `ReviewDecision` | Human review path when used. |
| `RollbackPlan` / `RollbackResult` | Recovery posture when rollback ran or was required. |
| `RDEResult` | `evaluation_kind`, `evidence_basis` when RDE path executed. |
| `RelationContext` | Relation-state hints for policy / history (not sole authority). |
| `AuditEvent` | Append-only audit references (`event_id` chain). |
| Policy / gate rationale | Best-effort notes where the runtime or policy layer recorded them. |

---

## 3. `EvidenceHandoff` fields — required, optional, and audit

Implementation reference: `EvidenceHandoff` in `openayane_rde.institution.models`.

### 3.1 Required bridge fields (model contract)

These fields are **always required** on `EvidenceHandoff`:

| Field | Requirement |
|---|---|
| `handoff_id` | Stable identifier for this handoff record. |
| `contract_id` | Links to the governing `ExecutionTaskContract`. |
| `tool_call_id` | Links to the tool execution subject. |
| `explanation` | Human-readable summary of what is being handed off and known gaps. |
| `created_at` | UTC timestamp for ordering and audit correlation. |

### 3.2 Strongly recommended for audit-grade handoff

| Field | Requirement |
|---|---|
| `audit_event_ids` | References into the Phase 3 audit trail. SHOULD be non-empty when any gate, execution, review, or rollback event was recorded. If empty, `explanation` MUST state why (e.g. synthetic test path with no audit append). |
| `evidence_basis` | SHOULD align with `RDEResult.evidence_basis` when RDE ran; otherwise SHOULD list the actual bases used (e.g. tool risk rule, execution contract). Values follow `EvidenceBasis` in `openayane_rde.core.models`. |

### 3.3 Optional / best-effort identifiers

Any of the following MAY be set when the corresponding Phase 3 object exists:

| Field | When to populate |
|---|---|
| `gate_decision_id` | When an `ExecutionGateDecision` record exists for this path. |
| `review_request_id` | When review was requested. |
| `review_decision_id` | When a `ReviewDecision` exists. |
| `execution_id` | When the runtime exposes a stable execution correlation id. |
| `rde_result_id` | When post-execution RDE produced an `RDEResult` reference. |

---

## 4. Policy halt vs RDE halt

Phase 3 may produce halt-like outcomes from **policy**, **RDE**, **runtime**, **review**, or later **institutional** layers. They MUST NOT be flattened into a single undifferentiated “halt” in downstream semantics.

- Use `HaltProvenance` (`halt_kind`, `evidence_basis`, optional `policy_rule_id` / `rde_result_id` / `audit_event_id`, `explanation`) when serializing halt provenance alongside or inside the evidence narrative (see `docs/40_openayane_rde_phase4_institution_bridge_spec.md` §5).
- A **policy halt** is not an **RDE halt**: preserve the distinction in handoff text and in any structured halt payload.

---

## 5. Review decisions and reviewer authority

- `review_decision_id` links to a Phase 3 review record; it does **not** prove institutional authority. Phase 4 authority checks use `ReviewerAuthority` / `AuthorityRef` models, not `reviewer_id` alone (`docs/40_openayane_rde_phase4_institution_bridge_spec.md`).
- When review did not occur, omit review IDs and state that explicitly in `explanation`.

---

## 6. Rollback plan and rollback result

- When `RollbackPlan` / `RollbackResult` exist, handoff SHOULD reference their audit or correlation identifiers where available.
- When reversibility is unknown or rollback did not complete, say so in `explanation`. Phase 4 MUST NOT infer reversibility from silence (see §7).

---

## 7. Missing evidence — required behaviour

When evidence is incomplete:

| Situation | Behaviour |
|---|---|
| No audit IDs though execution occurred | Treat as **handoff gap**: document in `explanation`; Phase 4 MUST NOT assume audit completeness. Prefer institutional outcomes such as `require_more_evidence` or conservative escalation when bridge logic runs (see `InstitutionalDecision` in code/spec). |
| RDE expected but no `rde_result_id` | Do not infer RDE classification; record actual path in `evidence_basis` / `explanation`. |
| Review implied but IDs missing | Do not infer approval; missing review is not approval. |
| Authority / reversibility unknown | MUST NOT be inferred from absent fields. |

These rules align with the irreversibility table in `docs/40_openayane_rde_phase4_institution_bridge_spec.md` §6 — **unknown_reversibility** and missing evidence both demand conservative institutional handling.

---

## 8. Synchronization policy

- Keep this document aligned with `EvidenceHandoff`, `InstitutionalDecision`, `HaltProvenance`, and deterministic `InstitutionBridge` behaviour as they evolve (Issues P4-1 through P4-4).
- Any rename of JSON or model fields MUST be reflected here and in `docs/40_openayane_rde_phase4_institution_bridge_spec.md`.

---

## 9. Document history

| Version | Date | Note |
|---|---|---|
| 0.1 | 2026-05-05 | Initial design note for Issue #32. |
