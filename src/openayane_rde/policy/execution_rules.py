"""Execution gate policy rules (Phase 3)."""

from __future__ import annotations

from typing import assert_never

from pydantic import BaseModel, Field

from openayane_rde.core.models import (
    ExecutionGatePolicyAction,
    RelationContext,
    RDEClassification,
    RDEResult,
    ToolCallRisk,
)


class ExecutionPolicyConfig(BaseModel):
    """Tunable execution gate behaviour."""

    allow_auto_execute_low_risk: bool = True
    allow_auto_execute_medium_risk: bool = False
    require_review_for_external_side_effects: bool = True
    require_review_for_protected_resources: bool = True
    halt_on_critical_risk: bool = True
    allow_dry_run_for_high_risk: bool = True
    min_trust_for_auto_execute: float = Field(default=0.5, ge=0.0, le=1.0)
    min_stability_for_auto_execute: float = Field(default=0.4, ge=0.0, le=1.0)

    model_config = {"extra": "forbid"}


def synthetic_rde_for_tool(contract_id: str, risk: ToolCallRisk) -> RDEResult:
    """Minimal RDEResult derived from tool risk (pre-diff gate path)."""

    cls: RDEClassification
    if risk.risk_level == "critical":
        cls = "critical_corruption"
    elif risk.risk_level == "high":
        cls = "suspicious_drift"
    elif risk.risk_level == "medium":
        cls = "authorized_deviation"
    else:
        cls = "preserved"

    req = (
        "halt"
        if cls == "critical_corruption"
        else "human_review"
        if cls == "suspicious_drift"
        else "approve_with_notes"
        if cls == "authorized_deviation"
        else "approve"
    )

    return RDEResult(
        contract_id=contract_id,
        classification=cls,
        risk_level=risk.risk_level,
        resonance_score=1.0 - risk.risk_score,
        preservation_score=max(0.0, 1.0 - risk.risk_score),
        authorization_score=max(0.0, 1.0 - risk.risk_score),
        violated_constraints=[],
        suspicious_elements=[],
        required_action=req,  # type: ignore[arg-type]
        explanation="Synthetic tool-call classification from ToolCallRisk.",
        metadata={"source": "phase3_execution_gate"},
    )


def decide_execution_policy_action(
    risk: ToolCallRisk,
    rde: RDEResult | None,
    relation_context: RelationContext | None,
    cfg: ExecutionPolicyConfig,
) -> tuple[ExecutionGatePolicyAction, str]:
    """Map risk + RDE + relation history to gate policy action."""

    if rde is not None and rde.classification == "critical_corruption":
        return "halt", "RDE classification critical_corruption."

    if risk.risk_level == "critical":
        if cfg.halt_on_critical_risk:
            return "halt", "ToolCallRisk critical."
        return "human_review", "Critical risk; halt disabled — escalate to review."

    trust = relation_context.trust if relation_context else 0.5
    stability = relation_context.stability if relation_context else 0.5

    if risk.unknown_target:
        return "human_review", "Unknown execution target."

    if cfg.require_review_for_protected_resources and risk.protected_resource_touched:
        return "human_review", "Protected resource touched."

    if cfg.require_review_for_external_side_effects and risk.external_side_effect:
        return "human_review", "External side effect."

    if risk.risk_level == "high":
        if not risk.rollback_possible:
            return "human_review", "High risk without rollback."
        if risk.external_side_effect:
            return "human_review", "High risk with external side effect."
        if cfg.allow_dry_run_for_high_risk:
            return "dry_run_only", "High risk — dry-run only."
        return "human_review", "High risk."

    if risk.risk_level == "medium":
        if trust < cfg.min_trust_for_auto_execute or stability < cfg.min_stability_for_auto_execute:
            return "human_review", "Medium risk with low trust or stability."
        if cfg.allow_auto_execute_medium_risk:
            return "approve_with_notes", "Medium risk auto path."
        return "dry_run_only", "Medium risk — dry-run only."

    if risk.risk_level == "low":
        if (
            trust >= cfg.min_trust_for_auto_execute
            and stability >= cfg.min_stability_for_auto_execute
            and cfg.allow_auto_execute_low_risk
        ):
            return "approve", "Low risk with sufficient relation trust."
        if cfg.allow_auto_execute_low_risk:
            return "approve_with_notes", "Low risk."
        return "human_review", "Low risk but auto-execute disabled."

    assert_never(risk.risk_level)
