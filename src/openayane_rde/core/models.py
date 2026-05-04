"""Shared Pydantic v2 data models for OpenAyane RDE Phase 1."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from openayane_rde.core.ids import new_id
from openayane_rde.core.time import now_utc

_SHA256_HEX_PATTERN = re.compile(r"^sha256:[a-fA-F0-9]{64}$")

# ---------------------------------------------------------------------------
# Enums (represented as Literal types for easy extensibility)
# ---------------------------------------------------------------------------

ContractMode = Literal["preservation", "creative", "refactor", "research", "execution"]

ProtectedElementKind = Literal[
    "claims",
    "definitions",
    "numbers",
    "dates",
    "citations",
    "references",
    "constraints",
    "headings",
    "schema_keys",
    "required_fields",
    "types",
    "function_signatures",
    "public_api",
    "imports",
    "tests",
    "safety_conditions",
    "permissions",
    "credentials",
]

ReviewAction = Literal["auto_approve", "approve_with_note", "human_review"]
ReviewActionDrift = Literal["human_review", "request_revision"]
ReviewActionCritical = Literal["halt", "rollback"]
ReviewActionBenign = Literal["approve_with_note", "human_review"]

OutputType = Literal["full_text", "patch", "plan", "tool_call"]
ProviderKind = Literal["openai", "anthropic", "google", "local", "tool", "mock", "unknown"]

DiffDomain = Literal["markdown", "json", "python", "generic"]
RiskHint = Literal["low", "medium", "high", "critical", "unknown"]
ChangeType = Literal["changed", "added", "deleted", "moved"]

RDEClassification = Literal[
    "preserved",
    "authorized_deviation",
    "benign_incidental_drift",
    "suspicious_drift",
    "critical_corruption",
    "creative_deviation",
]
RiskLevel = Literal["low", "medium", "high", "critical"]
RequiredAction = Literal[
    "approve",
    "approve_with_notes",
    "request_revision",
    "human_review",
    "halt",
    "rollback",
]

ActorKind = Literal[
    "user", "agent", "generator", "rde", "policy", "runtime", "reviewer", "system"
]
AuditActionKind = Literal[
    "create_contract",
    "generate_output",
    "run_structural_diff",
    "estimate_semantic_delta",
    "evaluate_rde",
    "make_policy_decision",
    "apply_change",
    "reject_change",
    "halt",
    "rollback",
    "request_human_review",
    "submit_human_review",
    "update_relation_store",
    "error",
]

PolicyActionKind = Literal[
    "approve",
    "approve_with_notes",
    "request_revision",
    "human_review",
    "halt",
    "rollback",
]

# ---------------------------------------------------------------------------
# TaskContract
# ---------------------------------------------------------------------------


class TargetScope(BaseModel):
    files: list[str] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=list)
    sections: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OutputPolicy(BaseModel):
    require_patch: bool
    require_change_report: bool
    require_uncertainty_report: bool

    model_config = {"extra": "forbid"}


class ReviewPolicy(BaseModel):
    preserved: ReviewAction
    authorized_deviation: ReviewAction
    benign_incidental_drift: ReviewActionBenign
    suspicious_drift: ReviewActionDrift
    critical_corruption: ReviewActionCritical

    model_config = {"extra": "forbid"}


class TaskContract(BaseModel):
    contract_id: str = Field(default_factory=lambda: new_id("tc"))
    mode: ContractMode
    target_scope: TargetScope
    requested_action: str
    allowed_delta_m: list[str] = Field(default_factory=list)
    forbidden_delta_m: list[str] = Field(default_factory=list)
    protected_elements: list[ProtectedElementKind] = Field(default_factory=list)
    output_policy: OutputPolicy
    review_policy: ReviewPolicy
    relation_context_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now_utc)

    model_config = {"extra": "forbid"}


# ---------------------------------------------------------------------------
# GeneratorOutput
# ---------------------------------------------------------------------------


class SelfReport(BaseModel):
    changed_elements: list[str] = Field(default_factory=list)
    unchanged_elements: list[str] = Field(default_factory=list)
    added_elements: list[str] = Field(default_factory=list)
    deleted_elements: list[str] = Field(default_factory=list)
    semantic_risk_notes: list[str] = Field(default_factory=list)
    uncertainty_notes: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class ModelInfo(BaseModel):
    provider: ProviderKind
    model: str
    temperature: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class GeneratorOutput(BaseModel):
    output_id: str = Field(default_factory=lambda: new_id("go"))
    contract_id: str
    output_type: OutputType
    payload: str | dict[str, Any] | list[Any]
    self_report: SelfReport
    model_info: ModelInfo
    created_at: datetime = Field(default_factory=now_utc)

    model_config = {"extra": "forbid"}


# ---------------------------------------------------------------------------
# StructuralDiff
# ---------------------------------------------------------------------------


class DiffNode(BaseModel):
    path: str
    kind: str
    before: Any = None
    after: Any = None
    description: str
    risk_hint: RiskHint = "unknown"

    model_config = {"extra": "allow"}


class ProtectedChange(BaseModel):
    element: str
    path: str
    change_type: ChangeType
    description: str
    risk_hint: RiskHint = "unknown"

    model_config = {"extra": "forbid"}


class Violation(BaseModel):
    path: str
    violation_type: str
    description: str
    risk_hint: RiskHint = "unknown"

    model_config = {"extra": "allow"}


class SelfReportMismatch(BaseModel):
    reported: str
    actual: str
    description: str
    risk_hint: RiskHint = "unknown"

    model_config = {"extra": "forbid"}


class StructuralDiff(BaseModel):
    diff_id: str = Field(default_factory=lambda: new_id("sdiff"))
    contract_id: str
    domain: DiffDomain
    changed_nodes: list[DiffNode] = Field(default_factory=list)
    added_nodes: list[DiffNode] = Field(default_factory=list)
    deleted_nodes: list[DiffNode] = Field(default_factory=list)
    moved_nodes: list[DiffNode] = Field(default_factory=list)
    protected_element_changes: list[ProtectedChange] = Field(default_factory=list)
    schema_violations: list[Violation] = Field(default_factory=list)
    signature_changes: list[DiffNode] = Field(default_factory=list)
    reference_breaks: list[Violation] = Field(default_factory=list)
    self_report_mismatches: list[SelfReportMismatch] = Field(default_factory=list)
    diff_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now_utc)

    model_config = {"extra": "forbid"}


# ---------------------------------------------------------------------------
# SemanticDelta (Phase 1 stub)
# ---------------------------------------------------------------------------


class SemanticDelta(BaseModel):
    delta_id: str = Field(default_factory=lambda: new_id("sdelta"))
    contract_id: str
    delta_m_score: float = Field(default=0.0, ge=0.0, le=1.0)
    changed_claims: list[str] = Field(default_factory=list)
    changed_constraints: list[str] = Field(default_factory=list)
    changed_definitions: list[str] = Field(default_factory=list)
    changed_numbers: list[str] = Field(default_factory=list)
    changed_references: list[str] = Field(default_factory=list)
    changed_safety_conditions: list[str] = Field(default_factory=list)
    semantic_equivalence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    uncertainty: float = Field(default=0.0, ge=0.0, le=1.0)
    is_stub: bool = True
    created_at: datetime = Field(default_factory=now_utc)

    model_config = {"extra": "forbid"}


# ---------------------------------------------------------------------------
# RDEResult
# ---------------------------------------------------------------------------


class ConstraintViolation(BaseModel):
    constraint: str
    path: str | None = None
    description: str
    severity: RiskLevel

    model_config = {"extra": "forbid"}


class SuspiciousElement(BaseModel):
    element: str
    path: str
    description: str
    risk_hint: RiskHint

    model_config = {"extra": "forbid"}


class ScoreDetails(BaseModel):
    structural_risk_score: float = 0.0
    semantic_delta_score: float = 0.0
    self_report_mismatch_score: float = 0.0
    relation_adjustment_score: float = 0.0

    model_config = {"extra": "allow"}


class RDEResult(BaseModel):
    result_id: str = Field(default_factory=lambda: new_id("rde"))
    contract_id: str
    classification: RDEClassification
    resonance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    preservation_score: float = Field(default=0.0, ge=0.0, le=1.0)
    authorization_score: float = Field(default=0.0, ge=0.0, le=1.0)
    risk_level: RiskLevel
    violated_constraints: list[ConstraintViolation] = Field(default_factory=list)
    suspicious_elements: list[SuspiciousElement] = Field(default_factory=list)
    required_action: RequiredAction
    explanation: str
    score_details: ScoreDetails | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now_utc)

    model_config = {"extra": "forbid"}


# ---------------------------------------------------------------------------
# PolicyDecision
# ---------------------------------------------------------------------------


class PolicyDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: new_id("pd"))
    contract_id: str
    rde_result_id: str
    action: PolicyActionKind
    rationale: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now_utc)

    model_config = {"extra": "forbid"}


# ---------------------------------------------------------------------------
# AuditEvent
# ---------------------------------------------------------------------------


class AuditError(BaseModel):
    error_type: str
    message: str
    recoverable: bool

    model_config = {"extra": "allow"}


class AuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: new_id("audit"))
    timestamp: datetime = Field(default_factory=now_utc)
    actor: ActorKind
    task_contract_id: str | None = None
    generator_output_id: str | None = None
    structural_diff_id: str | None = None
    semantic_delta_id: str | None = None
    rde_result_id: str | None = None
    policy_decision_id: str | None = None
    execution_result_id: str | None = None
    action: AuditActionKind
    hash_before: str | None = None
    hash_after: str | None = None
    explanation: str
    payload: dict[str, Any] = Field(default_factory=dict)
    error: AuditError | None = None

    model_config = {"extra": "forbid"}

    @field_validator("hash_before", "hash_after", mode="before")
    @classmethod
    def validate_hash(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not isinstance(v, str) or _SHA256_HEX_PATTERN.fullmatch(v) is None:
            raise ValueError(
                f"Hash must match sha256:<64 hex digits>, got: {v!r}"
            )
        return v


# ---------------------------------------------------------------------------
# RelationContext
# ---------------------------------------------------------------------------


class RelationContext(BaseModel):
    subject_id: str = "unknown"
    object_id: str = "unknown"
    trust: float = Field(default=0.5, ge=0.0, le=1.0)
    stability: float = Field(default=0.5, ge=0.0, le=1.0)
    context_affinity: float = Field(default=0.5, ge=0.0, le=1.0)
    interaction_count: int = 0
    last_delta_m: float = 0.0
    drift_patterns: list[str] = Field(default_factory=list)
    last_updated_at: datetime | None = None

    model_config = {"extra": "forbid"}


# ---------------------------------------------------------------------------
# ExecutionResult
# ---------------------------------------------------------------------------


class ExecutionResult(BaseModel):
    execution_id: str = Field(default_factory=lambda: new_id("exec"))
    contract_id: str
    policy_decision_id: str
    outcome: Literal["applied", "halted", "rejected", "pending_review"]
    explanation: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now_utc)

    model_config = {"extra": "forbid"}
