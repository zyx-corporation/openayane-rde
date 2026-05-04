"""RDE minimal classifier for Phase 1.

Classifications:
  preserved
  authorized_deviation
  suspicious_drift
  critical_corruption

Optional (Phase 1):
  benign_incidental_drift
  creative_deviation
"""

from __future__ import annotations

from openayane_rde.core.models import (
    RDEClassification,
    RequiredAction,
    RiskLevel,
    StructuralDiff,
    TaskContract,
)


def classify(
    preservation_score: float,
    authorization_score: float,
    structural_risk_score: float,
    self_report_mismatch_score: float,
    structural_diff: StructuralDiff,
    contract: TaskContract,
) -> tuple[RDEClassification, RiskLevel, RequiredAction]:
    """Classify the deviation and return (classification, risk_level, required_action).

    Phase 1 rule-based classifier. Priority from highest to lowest:
    1. critical_corruption – any critical protected change or schema violation
    2. suspicious_drift – protected change exists or high mismatch
    3. authorized_deviation – changes exist but within allowed scope
    4. preserved – no meaningful change detected
    """
    has_critical_protected = any(
        pc.risk_hint in ("critical",)
        for pc in structural_diff.protected_element_changes
    )
    has_schema_violation = len(structural_diff.schema_violations) > 0
    has_critical_mismatch = any(
        m.risk_hint == "critical"
        for m in structural_diff.self_report_mismatches
    )

    if has_critical_protected or has_schema_violation or has_critical_mismatch:
        return "critical_corruption", "critical", "halt"

    has_any_protected_change = len(structural_diff.protected_element_changes) > 0
    has_high_mismatch = self_report_mismatch_score >= 0.4

    if has_any_protected_change or has_high_mismatch:
        risk = _compute_risk(structural_risk_score)
        return "suspicious_drift", risk, "human_review"

    total_changes = (
        len(structural_diff.changed_nodes)
        + len(structural_diff.deleted_nodes)
        + len(structural_diff.added_nodes)
    )

    if total_changes > 0 and contract.allowed_delta_m:
        return "authorized_deviation", "low", "approve_with_notes"

    if total_changes > 0 and not contract.allowed_delta_m:
        return "suspicious_drift", "medium", "human_review"

    return "preserved", "low", "approve"


def _compute_risk(structural_risk_score: float) -> RiskLevel:
    if structural_risk_score >= 0.7:
        return "critical"
    if structural_risk_score >= 0.4:
        return "high"
    if structural_risk_score >= 0.2:
        return "medium"
    return "low"
