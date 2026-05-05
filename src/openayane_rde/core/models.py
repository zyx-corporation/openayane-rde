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

SemanticDeltaMode = Literal["stub", "structural_baseline", "llm_evaluator"]

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

# Pre-execution gate uses synthetic classification; Phase 1 / post-exec use structural diff.
RdeEvaluationKind = Literal["pre_synthetic", "post_structural"]

# What evidence the RDE classification was derived from (orthogonal to evaluation_kind).
EvidenceBasis = Literal[
    "tool_risk_rule",
    "execution_contract",
    "structural_diff",
    "semantic_delta",
    "observed_side_effects",
    "rollback_result",
    "human_review_decision",
    "llm_assisted_semantic_evaluation",
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
    # Phase 3 execution / review / rollback audit kinds
    "execution_gate_evaluated",
    "execution_blocked",
    "execution_approved",
    "execution_dry_run_completed",
    "execution_completed",
    "execution_failed",
    "execution_timed_out",
    "human_review_requested",
    "human_review_decided",
    "rollback_plan_created",
    "rollback_completed",
    "rollback_failed",
    "semantic_evaluation_completed",
]

PolicyActionKind = Literal[
    "approve",
    "approve_with_notes",
    "request_revision",
    "human_review",
    "halt",
    "rollback",
]

ExecutionGatePolicyAction = Literal[
    "approve",
    "approve_with_notes",
    "dry_run_only",
    "human_review",
    "halt",
]

ExecutionActionType = Literal[
    "read",
    "write",
    "delete",
    "execute",
    "network",
    "external_api",
    "repository_patch",
    "unknown",
]
ExternalSideEffectKind = Literal[
    "none",
    "read_only_fetch",
    "state_changing_request",
    "notification",
    "publishing",
    "payment_or_billing",
    "identity_or_auth",
    "data_exfiltration_risk",
    "legal_or_compliance_effect",
    "unknown",
]

RollbackStrategyKind = Literal[
    "none",
    "file_snapshot",
    "git_patch_reverse",
    "transactional",
    "manual",
]

ToolExecutionStatus = Literal[
    "not_executed",
    "dry_run_completed",
    "completed",
    "failed",
    "timed_out",
    "blocked",
]

ReviewRequestStatus = Literal[
    "pending",
    "approved",
    "rejected",
    "revision_requested",
    "expired",
]

ReviewerDecisionKind = Literal[
    "approve",
    "approve_dry_run",
    "reject",
    "request_revision",
    "require_rollback_plan",
]

SemanticEvaluatorRecommendation = Literal[
    "no_issue",
    "approve_with_notes",
    "human_review",
    "halt",
]

RelationType = Literal[
    "generator-document",
    "agent-document",
    "user-agent",
    "tool-workspace",
    "domain-policy",
]

DriftPatternKind = Literal[
    "citation_weakening",
    "citation_deletion",
    "number_change",
    "definition_shift",
    "constraint_omission",
    "schema_key_deletion",
    "required_field_deletion",
    "signature_change",
    "test_deletion",
    "self_report_mismatch",
    "other",
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
    semantic_mode: SemanticDeltaMode = "stub"
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
    evaluation_kind: RdeEvaluationKind | None = None
    evidence_basis: list[EvidenceBasis] = Field(default_factory=list)
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
    drift_pattern_counts: dict[str, int] = Field(default_factory=dict)
    review_threshold_adjustment: float = Field(default=0.0, ge=0.0, le=1.0)
    generator_reliability_score: float | None = Field(default=None, ge=0.0, le=1.0)
    document_fragility_score: float | None = Field(default=None, ge=0.0, le=1.0)
    last_updated_at: datetime | None = None

    model_config = {"extra": "forbid"}


class DriftPattern(BaseModel):
    pattern_id: str = Field(default_factory=lambda: new_id("dp"))
    kind: DriftPatternKind
    count: int = 1
    severity: RiskLevel = "medium"
    examples: list[str] = Field(default_factory=list)
    last_seen_at: datetime = Field(default_factory=now_utc)

    model_config = {"extra": "forbid"}


class GeneratorReliabilityProfile(BaseModel):
    generator_id: str
    total_outputs: int = 0
    self_report_mismatch_count: int = 0
    critical_corruption_count: int = 0
    suspicious_drift_count: int = 0
    preserved_count: int = 0
    authorized_deviation_count: int = 0
    reliability_score: float = Field(default=1.0, ge=0.0, le=1.0)

    model_config = {"extra": "forbid"}


class DocumentFragilityProfile(BaseModel):
    document_id: str
    total_edits: int = 0
    protected_change_count: int = 0
    citation_break_count: int = 0
    number_change_count: int = 0
    definition_shift_count: int = 0
    fragility_score: float = Field(default=0.0, ge=0.0, le=1.0)

    model_config = {"extra": "forbid"}


class RelationStoreRecord(BaseModel):
    relation_id: str = Field(default_factory=lambda: new_id("rel"))
    subject_id: str
    object_id: str
    relation_type: RelationType = "generator-document"
    trust: float = Field(default=0.5, ge=0.0, le=1.0)
    stability: float = Field(default=0.5, ge=0.0, le=1.0)
    context_affinity: float = Field(default=0.5, ge=0.0, le=1.0)
    interaction_count: int = 0
    critical_corruption_count: int = 0
    suspicious_drift_count: int = 0
    self_report_mismatch_count: int = Field(
        0,
        description=(
            "Number of evaluations that included at least one self-report mismatch."
        ),
    )
    self_report_mismatch_item_count: int = Field(
        0,
        description="Cumulative count of self-report mismatch rows across evaluations.",
    )
    drift_patterns: list[DriftPattern] = Field(default_factory=list)
    generator_reliability_profile: GeneratorReliabilityProfile | None = None
    document_fragility_profile: DocumentFragilityProfile | None = None
    review_threshold_adjustment: float = Field(default=0.0, ge=0.0, le=1.0)
    last_delta_m: float = 0.0
    last_audit_event_id: str | None = None
    updated_at: datetime = Field(default_factory=now_utc)

    model_config = {"extra": "forbid"}


class AllowedDeltaMatchResult(BaseModel):
    matched_changes: list[str] = Field(default_factory=list)
    unmatched_changes: list[str] = Field(default_factory=list)
    forbidden_matches: list[str] = Field(default_factory=list)
    match_score: float = Field(default=0.0, ge=0.0, le=1.0)
    explanation: str = ""

    model_config = {"extra": "forbid"}


class RelationUpdateSummary(BaseModel):
    """Outcome of applying Phase 1 evaluation data to relation state (Phase 2 hook)."""

    context: RelationContext
    updated: bool = False
    relation_id: str | None = None
    trust_before: float | None = None
    trust_after: float | None = None
    stability_before: float | None = None
    stability_after: float | None = None
    review_threshold_adjustment_before: float | None = None
    review_threshold_adjustment_after: float | None = None
    updated_patterns: list[str] = Field(default_factory=list)
    message: str = ""

    model_config = {"extra": "forbid"}


# ---------------------------------------------------------------------------
# Phase 3: Agent execution gate, tool contracts, review (see Phase 3 spec)
# ---------------------------------------------------------------------------


class ToolCallRequest(BaseModel):
    tool_call_id: str
    agent_id: str
    tool_name: str
    action_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    target_resources: list[str] = Field(default_factory=list)
    declared_purpose: str | None = None
    agent_self_report: str | None = None
    created_at: datetime = Field(default_factory=now_utc)

    model_config = {"extra": "forbid"}


class ExecutionTaskContract(BaseModel):
    contract_id: str = Field(default_factory=lambda: new_id("etc"))
    source_tool_call_id: str
    agent_id: str
    action_type: ExecutionActionType
    tool_name: str
    target_resources: list[str] = Field(default_factory=list)
    expected_side_effects: list[str] = Field(default_factory=list)
    allowed_side_effects: list[str] = Field(default_factory=list)
    forbidden_side_effects: list[str] = Field(default_factory=list)
    protected_resources: list[str] = Field(default_factory=list)
    rollback_strategy: RollbackStrategyKind = "none"
    rollback_required: bool = False
    required_user_approval: bool = False
    max_runtime_ms: int | None = None
    max_output_bytes: int | None = None
    network_allowed: bool = False
    external_side_effect_kind: ExternalSideEffectKind = "none"
    allowed_network_domains: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=now_utc)

    model_config = {"extra": "forbid"}


class ToolCallRisk(BaseModel):
    risk_level: RiskLevel
    risk_score: float = Field(ge=0.0, le=1.0, default=0.0)
    irreversible: bool = False
    external_side_effect: bool = False
    protected_resource_touched: bool = False
    rollback_possible: bool = False
    unknown_target: bool = False
    reasons: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class ExecutionGateDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: new_id("egd"))
    contract_id: str
    policy_action: ExecutionGatePolicyAction
    reason: str
    risk: ToolCallRisk
    rde_result: RDEResult | None = None
    relation_context: RelationContext | None = None
    rollback_plan_required: bool = False
    review_request_id: str | None = None
    audit_event_id: str | None = None
    policy_adjustment_notes: list[str] = Field(
        default_factory=list,
        description="Relation-history escalations aligned with Phase 1 policy bridge rules.",
    )
    created_at: datetime = Field(default_factory=now_utc)

    model_config = {"extra": "forbid"}


class ExecutionGateEvaluation(BaseModel):
    """Pre-execution gate outcome: policy decision plus the task contract used for execution."""

    decision: ExecutionGateDecision
    contract: ExecutionTaskContract

    model_config = {"extra": "forbid"}


class ToolExecutionResult(BaseModel):
    """Outcome of Safe Execution Runtime (Phase 3 spec: ExecutionResult)."""

    execution_id: str = Field(default_factory=lambda: new_id("tex"))
    contract_id: str
    tool_call_id: str
    status: ToolExecutionStatus
    exit_code: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    changed_resources: list[str] = Field(default_factory=list)
    observed_side_effects: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    rollback_plan_id: str | None = None
    error_message: str | None = None
    policy_decision_id: str | None = None
    audit_event_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now_utc)

    model_config = {"extra": "forbid"}


class PostExecutionDiff(BaseModel):
    diff_id: str = Field(default_factory=lambda: new_id("ped"))
    contract_id: str
    before_snapshot_id: str | None = None
    after_snapshot_id: str | None = None
    changed_resources: list[str] = Field(default_factory=list)
    unexpected_side_effects: list[str] = Field(default_factory=list)
    protected_resource_changes: list[str] = Field(default_factory=list)
    structural_diff: StructuralDiff | None = None
    semantic_delta: SemanticDelta | None = None
    created_at: datetime = Field(default_factory=now_utc)

    model_config = {"extra": "forbid"}


class RollbackPlan(BaseModel):
    rollback_plan_id: str = Field(default_factory=lambda: new_id("rbp"))
    contract_id: str
    strategy: RollbackStrategyKind
    target_resources: list[str] = Field(default_factory=list)
    snapshot_refs: list[str] = Field(default_factory=list)
    reverse_patch_path: str | None = None
    manual_steps: list[str] = Field(default_factory=list)
    validated: bool = False
    validation_message: str | None = None
    created_at: datetime = Field(default_factory=now_utc)

    model_config = {"extra": "forbid"}


class RollbackResult(BaseModel):
    rollback_result_id: str = Field(default_factory=lambda: new_id("rbr"))
    rollback_plan_id: str
    status: Literal[
        "not_required",
        "completed",
        "failed",
        "manual_required",
        "not_possible",
    ]
    restored_resources: list[str] = Field(default_factory=list)
    error_message: str | None = None
    audit_event_id: str | None = None
    completed_at: datetime | None = None

    model_config = {"extra": "forbid"}


class ReviewRequest(BaseModel):
    review_request_id: str = Field(default_factory=lambda: new_id("rrq"))
    contract_id: str
    tool_call_id: str
    agent_id: str
    reason: str
    risk: ToolCallRisk
    proposed_action_summary: str = ""
    expected_side_effects: list[str] = Field(default_factory=list)
    forbidden_side_effects: list[str] = Field(default_factory=list)
    rollback_plan: RollbackPlan | None = None
    rde_result: RDEResult | None = None
    relation_context: RelationContext | None = None
    status: ReviewRequestStatus = "pending"
    created_at: datetime = Field(default_factory=now_utc)

    model_config = {"extra": "forbid"}


class ReviewDecision(BaseModel):
    review_decision_id: str = Field(default_factory=lambda: new_id("rvd"))
    review_request_id: str
    reviewer_id: str
    decision: ReviewerDecisionKind
    reason: str
    approved_at: datetime | None = None
    created_at: datetime = Field(default_factory=now_utc)

    model_config = {"extra": "forbid"}


class SemanticEvaluationRequest(BaseModel):
    evaluation_id: str = Field(default_factory=lambda: new_id("sevr"))
    contract_id: str
    tool_call_id: str
    phase: Literal["pre_execution", "post_execution"] = "pre_execution"
    created_at: datetime = Field(default_factory=now_utc)

    model_config = {"extra": "forbid"}


class SemanticEvaluationResult(BaseModel):
    evaluation_id: str = Field(default_factory=lambda: new_id("sev"))
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    suspected_delta_m: list[str] = Field(default_factory=list)
    preserved_elements: list[str] = Field(default_factory=list)
    transformed_elements: list[str] = Field(default_factory=list)
    inferred_extensions: list[str] = Field(default_factory=list)
    unresolved_elements: list[str] = Field(default_factory=list)
    drift_risks: list[str] = Field(default_factory=list)
    recommendation: SemanticEvaluatorRecommendation = "no_issue"
    explanation: str = ""
    created_at: datetime = Field(default_factory=now_utc)

    model_config = {"extra": "forbid"}


# ---------------------------------------------------------------------------
# ModificationOutcome (Phase 1 policy-driven apply / halt)
# ---------------------------------------------------------------------------


class ModificationOutcome(BaseModel):
    """Phase 1: result of ``apply_or_halt`` (would-apply vs halt vs pending review)."""

    outcome_id: str = Field(default_factory=lambda: new_id("exec"))
    contract_id: str
    policy_decision_id: str
    outcome: Literal["applied", "halted", "rejected", "pending_review"]
    explanation: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now_utc)

    model_config = {"extra": "forbid"}
