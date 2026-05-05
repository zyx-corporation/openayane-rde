---
title: "OpenAyane RDE Phase 4 Institution Bridge Specification"
version: "0.2"
date: "2026-05-05"
status: "draft-specification"
---

# OpenAyane RDE Phase 4 Institution Bridge Specification

## 0. Purpose

Phase 4 defines the bridge between Phase 3 execution governance and an institutional governance layer.

Phase 3 answers:

```text
Should this tool action proceed, halt, require review, or run under constraints?
```

Phase 4 answers:

```text
Who or what has the authority to accept the consequence, under which institutional rule, with which evidence, and with what later accountability?
```

Phase 4 does not replace RDE, Policy, SafeExecutionRuntime, HumanReviewWorkflow, or RollbackManager. It receives their outputs as evidence and turns them into institutionally accountable decisions.

Related Phase 3 boundary: `docs/37_openayane_rde_phase3_exit_report.md`.

## 1. Scope

### 1.1 In scope

```text
- InstitutionRule model
- AuthorityRef model
- ReviewerAuthority model
- InstitutionalDecision model
- EvidenceHandoff model
- policy halt vs RDE halt distinction
- irreversible operation classification
- reviewer authority check interface
- audit linkage between Phase 3 and Phase 4
- minimal interface skeleton for future Institution layer
```

### 1.2 Out of scope

```text
- Full PoP-UID implementation
- cryptographic identity proof
- complete DAO / governance voting implementation
- production UI
- legal compliance engine
- OS-level sandbox
- cloud provider integration
```

These are future L3 / Phase 5+ concerns unless explicitly promoted.

## 2. Design principle

Phase 4 must not collapse institution into model judgement.

The core separation is:

```text
RDE: evaluates meaning change and drift risk.
Policy: maps evidence and relation state to allowed institutional actions.
Execution Gate: decides whether an action may enter runtime or review.
Human Review: records human or operator judgement.
Institution Bridge: checks whether the reviewer / actor has authority to accept the consequence.
AuditLog: records the evidence chain.
```

Institution Bridge is therefore an authority and accountability layer, not another semantic evaluator.

## 3. Phase 3 evidence inputs

Phase 4 consumes the following Phase 3 evidence inputs.

```text
- ToolCallRequest
- ExecutionTaskContract
- ToolCallRisk
- ExecutionGateDecision
- ToolExecutionResult
- ReviewRequest
- ReviewDecision
- RollbackPlan
- RollbackResult
- RDEResult
- RelationContext
- AuditEvent references
```

Required fields for initial bridge work:

```text
- contract_id
- tool_call_id
- agent_id
- action_type
- external_side_effect_kind
- risk_level
- policy_action
- evaluation_kind
- evidence_basis
- reviewer_id, if review exists
- audit_event_id
- rollback_strategy
- rollback_result status, if available
```

## 4. Core models

The following models are **draft specification targets**. They are Python-like sketches, not yet a committed schema contract.

When implementation starts, field names must be synchronized across:

```text
- Pydantic models under src/
- schemas/ JSON schema files, if serialized
- tests and fixtures
- docs/37 Phase 3 evidence handoff references
- audit payload field names
```

### 4.1 InstitutionRule

```python
class InstitutionRule(BaseModel):
    rule_id: str
    name: str
    description: str
    scope: list[str]
    applies_to_action_types: list[ExecutionActionType]
    applies_to_side_effects: list[ExternalSideEffectKind]
    minimum_authority_level: str
    requires_human_review: bool = False
    requires_rollback_plan: bool = False
    allows_irreversible_action: bool = False
    evidence_required: list[str]
    created_at: datetime
```

`InstitutionRule` defines the institutional condition under which an action may be accepted.

It must not encode every runtime rule. Runtime rules remain in Phase 3. InstitutionRule encodes accountability, authority, and consequence acceptance.

### 4.2 AuthorityRef

```python
class AuthorityRef(BaseModel):
    authority_id: str
    authority_type: Literal[
        "human_reviewer",
        "system_policy",
        "institution_delegate",
        "emergency_override",
        "external_authority",
    ]
    subject_id: str
    authority_level: str
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
```

`AuthorityRef` is a reference, not proof. Phase 4 can model authority references before full PoP-UID or cryptographic proof exists.

### 4.3 ReviewerAuthority

```python
class ReviewerAuthority(BaseModel):
    reviewer_id: str
    authority_refs: list[AuthorityRef]
    allowed_action_types: list[ExecutionActionType]
    allowed_side_effects: list[ExternalSideEffectKind]
    max_risk_level: RiskLevel
    can_approve_irreversible: bool = False
    can_override_halt: bool = False
```

This model prevents Human Review from becoming a rubber stamp.

### 4.4 EvidenceHandoff

```python
class EvidenceHandoff(BaseModel):
    handoff_id: str
    contract_id: str
    tool_call_id: str
    gate_decision_id: str | None = None
    review_request_id: str | None = None
    review_decision_id: str | None = None
    execution_id: str | None = None
    rde_result_id: str | None = None
    audit_event_ids: list[str] = Field(default_factory=list)
    evidence_basis: list[EvidenceBasis] = Field(default_factory=list)
    explanation: str
    created_at: datetime
```

`EvidenceHandoff` is the structured bridge object from Phase 3 to Phase 4.

### 4.5 InstitutionalDecision

```python
class InstitutionalDecision(BaseModel):
    institutional_decision_id: str
    handoff_id: str
    rule_id: str | None = None
    authority_id: str | None = None
    decision: Literal[
        "accept",
        "reject",
        "require_more_evidence",
        "require_higher_authority",
        "halt_institutionally",
        "record_only",
    ]
    rationale: str
    risk_accepted: bool = False
    irreversible_accepted: bool = False
    audit_event_id: str | None = None
    created_at: datetime
```

`InstitutionalDecision` is not an execution result. It is a consequence-acceptance record.

## 5. Policy halt vs RDE halt

Phase 4 must preserve the distinction between policy halt and RDE halt.

```text
policy halt:
  The action violates an institutional or operational rule before semantic evaluation is necessary.

RDE halt:
  The action/output is halted because RDE classified the meaning change or structural drift as unacceptable.
```

Initial payload recommendation:

```python
class HaltProvenance(BaseModel):
    halt_kind: Literal[
        "policy_halt",
        "rde_halt",
        "runtime_block",
        "review_rejection",
        "institutional_halt",
    ]
    evidence_basis: list[EvidenceBasis] = Field(default_factory=list)
    policy_rule_id: str | None = None
    rde_result_id: str | None = None
    audit_event_id: str | None = None
    explanation: str
```

This prevents UI and later audit from flattening all halt decisions into a single red state.

## 6. Irreversible operation classification

Phase 4 must classify irreversible or difficult-to-rollback actions.

Initial classes:

```text
reversible_local:
  Can be restored by local file snapshot or equivalent.

reversible_external:
  External system supports reliable rollback API.

manual_recovery:
  Recovery is possible but requires human or operator intervention.

not_reversible:
  No reliable rollback is available.

unknown_reversibility:
  Reversibility cannot be determined from available evidence.
```

Institutional approval requirements:

| Reversibility | Default institutional decision |
|---|---|
| reversible_local | accept if rule and authority match |
| reversible_external | require explicit rollback evidence |
| manual_recovery | require human authority and recovery plan |
| not_reversible | require higher authority or halt |
| unknown_reversibility | require more evidence or halt |

## 7. Minimal Phase 4 flow

```text
Phase 3 evidence
  -> EvidenceHandoff
  -> InstitutionRule matching
  -> ReviewerAuthority check
  -> InstitutionalDecision
  -> AuditLog append
```

Detailed flow:

```text
1. Receive ExecutionGateDecision and related evidence.
2. Build EvidenceHandoff.
3. Match InstitutionRule by action_type, external_side_effect_kind, risk, and reversibility.
4. If a ReviewDecision exists, verify ReviewerAuthority.
5. If no sufficient authority exists, return require_higher_authority or halt_institutionally.
6. If evidence is incomplete, return require_more_evidence.
7. If acceptable, record InstitutionalDecision.accept.
8. Append audit event and link event IDs.
```

Implementation guidance: the first Phase 4 implementation PR should remain a skeleton or model-only PR. Avoid adding UI, external integrations, or broad persistence before the authority model stabilizes.

## 8. Initial API sketch

```python
class InstitutionBridge(Protocol):
    def build_handoff(
        self,
        *,
        contract: ExecutionTaskContract,
        gate_decision: ExecutionGateDecision,
        execution_result: ToolExecutionResult | None = None,
        review_request: ReviewRequest | None = None,
        review_decision: ReviewDecision | None = None,
        rollback_plan: RollbackPlan | None = None,
        rollback_result: RollbackResult | None = None,
        rde_result: RDEResult | None = None,
    ) -> EvidenceHandoff: ...

    def decide(
        self,
        handoff: EvidenceHandoff,
        rules: list[InstitutionRule],
        reviewer_authority: ReviewerAuthority | None = None,
    ) -> InstitutionalDecision: ...
```

The first implementation should be deterministic and rule-based.

LLM-assisted explanation may be added later, but it must not be the decision authority.

## 9. Storage and audit

Phase 4 may initially store institutional decisions in SQLite or JSONL-linked local storage.

Minimal persistence table candidates:

```text
institution_rules
reviewer_authorities
institutional_decisions
evidence_handoffs
```

However, Phase 4 should not block on full persistence if the first PR is specification and interface skeleton only.

Audit requirements:

```text
- Every InstitutionalDecision must reference EvidenceHandoff.
- EvidenceHandoff must reference Phase 3 audit_event_ids where available.
- HaltProvenance must be represented when decision is halt-like.
- ReviewerAuthority check result must be explainable.
```

## 10. Tests required for first implementation PR

Minimum tests:

```text
- policy halt remains distinguishable from RDE halt
- reviewer without sufficient authority cannot approve high-risk action
- reviewer with sufficient authority can approve allowed high-risk action
- irreversible action requires higher authority or halt
- incomplete evidence returns require_more_evidence
- EvidenceHandoff preserves audit_event_ids and evidence_basis
```

## 11. Phase 4 issue seeds

Recommended initial issues:

```text
P4-1: Define InstitutionRule / AuthorityRef / ReviewerAuthority models
P4-2: Define EvidenceHandoff and InstitutionalDecision models
P4-3: Add HaltProvenance to preserve policy halt vs RDE halt distinction
P4-4: Implement deterministic InstitutionBridge decision function
P4-5: Add tests for reviewer authority and irreversible actions
P4-6: Document Phase 3 evidence handoff requirements
```

## 12. RDE differential review

### 12.1 Preserved elements

Phase 4 preserves the Phase 3 separation between RDE, Policy, Runtime, Review, Rollback, and AuditLog. It does not promote any one component into total authority.

### 12.2 Authorized transformations

Phase 3 execution evidence is transformed into institutional evidence. This is an authorized transformation because Phase 4 is explicitly about accountability and authority, not raw runtime control.

### 12.3 Inferred extensions

The following extensions are introduced by this specification:

```text
- InstitutionRule
- AuthorityRef
- ReviewerAuthority
- EvidenceHandoff
- InstitutionalDecision
- HaltProvenance
- irreversible operation classification
```

These extend OpenAyane from execution governance into institutional accountability.

### 12.4 Unresolved elements

The following remain unresolved:

```text
- full PoP-UID integration
- cryptographic authority proof
- UI for reviewer authority
- persistence migration strategy for institutional records
- mapping to external legal/compliance frameworks
```

### 12.5 Drift risks

Key drift risks:

```text
- Institution Bridge becomes another evaluator instead of an authority layer.
- Human review is treated as authority even when reviewer authority is not checked.
- Policy halt, runtime block, and RDE halt are flattened into one state.
- Rollback metadata is treated as proof of reversibility.
- Optional semantic evaluator output is used as an institutional decision.
```

### 12.6 Next update policy

The next Phase 4 document or PR should either:

```text
- implement the core models only, or
- create issues P4-1 through P4-6 without code changes.
```

Avoid starting with UI or external integrations before the authority model is stable.

## 13. Revision history

| Version | Date | Notes |
|---|---|---|
| 0.1 | 2026-05-05 | Initial Phase 4 Institution Bridge draft. |
| 0.2 | 2026-05-05 | Clarified draft-model status, schema synchronization policy, skeleton-first guidance, and Phase 3 exit link. |
