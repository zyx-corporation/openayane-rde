"""Phase 4 Institution Bridge — authority, rule, and evidence handoff models (skeleton).

These models implement the draft shapes in ``docs/40_openayane_rde_phase4_institution_bridge_spec.md``.
They are **not** production authority infrastructure (no PoP-UID, no cryptographic proof).
`EvidenceHandoff` / `InstitutionalDecision` are bridge records, not execution outcomes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from openayane_rde.core.models import (
    EvidenceBasis,
    ExecutionActionType,
    ExternalSideEffectKind,
    RiskLevel,
)

AuthorityType = Literal[
    "human_reviewer",
    "system_policy",
    "institution_delegate",
    "emergency_override",
    "external_authority",
]


class InstitutionRule(BaseModel):
    """Institutional condition under which an action may be accepted (accountability layer).

    Runtime execution rules remain Phase 3; this encodes institution-facing accountability.
    """

    rule_id: str = Field(min_length=1)
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


class AuthorityRef(BaseModel):
    """Reference to an authority source — not proof of authority."""

    authority_id: str = Field(min_length=1)
    authority_type: AuthorityType
    subject_id: str
    authority_level: str
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReviewerAuthority(BaseModel):
    """Maps a reviewer identity to bounded authority — avoids rubber-stamp review."""

    reviewer_id: str = Field(min_length=1)
    authority_refs: list[AuthorityRef]
    allowed_action_types: list[ExecutionActionType]
    allowed_side_effects: list[ExternalSideEffectKind]
    max_risk_level: RiskLevel
    can_approve_irreversible: bool = False
    can_override_halt: bool = False


InstitutionalDecisionKind = Literal[
    "accept",
    "reject",
    "require_more_evidence",
    "require_higher_authority",
    "halt_institutionally",
    "record_only",
]


class EvidenceHandoff(BaseModel):
    """Structured bridge from Phase 3 execution governance to Phase 4 accountability.

    References Phase 3 artefacts by ID; it does not reinterpret them as institutional truth.
    """

    handoff_id: str = Field(min_length=1)
    contract_id: str = Field(min_length=1)
    tool_call_id: str = Field(min_length=1)
    gate_decision_id: str | None = None
    review_request_id: str | None = None
    review_decision_id: str | None = None
    execution_id: str | None = None
    rde_result_id: str | None = None
    audit_event_ids: list[str] = Field(default_factory=list)
    evidence_basis: list[EvidenceBasis] = Field(default_factory=list)
    explanation: str
    created_at: datetime


class InstitutionalDecision(BaseModel):
    """Institutional consequence-acceptance record — not an execution or RDE result."""

    institutional_decision_id: str = Field(min_length=1)
    handoff_id: str = Field(min_length=1)
    rule_id: str | None = None
    authority_id: str | None = None
    decision: InstitutionalDecisionKind
    rationale: str
    risk_accepted: bool = False
    irreversible_accepted: bool = False
    audit_event_id: str | None = None
    created_at: datetime
