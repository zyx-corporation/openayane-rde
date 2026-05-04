"""RDE scoring functions for Phase 1.

Scores preservation, authorization, self-report mismatch, and risk.
All scoring is rule-based in Phase 1.
"""

from __future__ import annotations

from openayane_rde.core.models import (
    RelationContext,
    SemanticDelta,
    StructuralDiff,
    TaskContract,
)


def score_preservation(
    structural_diff: StructuralDiff,
    contract: TaskContract,
) -> float:
    """Score how well protected elements were preserved.

    Returns a value in [0.0, 1.0] where 1.0 means fully preserved.
    """
    protected = set(contract.protected_elements)
    if not protected:
        return 1.0

    num_violations = len(structural_diff.protected_element_changes)
    if num_violations == 0:
        return 1.0

    penalty = min(1.0, num_violations * 0.25)
    return max(0.0, 1.0 - penalty)


def score_authorization(
    structural_diff: StructuralDiff,
    contract: TaskContract,
    semantic_delta: SemanticDelta,
) -> float:
    """Score how well changes are covered by allowed_delta_m.

    Returns a value in [0.0, 1.0] where 1.0 means all changes authorized.
    """
    allowed = {a.lower() for a in contract.allowed_delta_m}
    if not allowed:
        total_changes = (
            len(structural_diff.changed_nodes)
            + len(structural_diff.deleted_nodes)
            + len(structural_diff.added_nodes)
        )
        if total_changes == 0:
            return 1.0
        return 0.0

    total_changes = (
        len(structural_diff.changed_nodes)
        + len(structural_diff.deleted_nodes)
        + len(structural_diff.added_nodes)
    )
    if total_changes == 0:
        return 1.0

    unauthorized = len(structural_diff.protected_element_changes)
    penalty = min(1.0, unauthorized / max(1, total_changes))
    return max(0.0, 1.0 - penalty)


def score_self_report_mismatch(
    structural_diff: StructuralDiff,
) -> float:
    """Score the degree of self-report mismatch.

    Returns a value in [0.0, 1.0] where 0.0 means no mismatch, 1.0 means severe.
    """
    num_mismatches = len(structural_diff.self_report_mismatches)
    if num_mismatches == 0:
        return 0.0
    return min(1.0, num_mismatches * 0.4)


def score_structural_risk(
    structural_diff: StructuralDiff,
    contract: TaskContract,
) -> float:
    """Score structural risk level.

    Returns a value in [0.0, 1.0] where 1.0 means maximum risk.
    """
    critical_changes = sum(
        1
        for pc in structural_diff.protected_element_changes
        if pc.risk_hint in ("critical", "high")
    )
    schema_violations = len(structural_diff.schema_violations)
    mismatch_critical = sum(
        1
        for m in structural_diff.self_report_mismatches
        if m.risk_hint == "critical"
    )

    raw = (
        critical_changes * 0.35
        + schema_violations * 0.3
        + mismatch_critical * 0.35
    )
    return min(1.0, raw)


def score_resonance(
    preservation: float,
    authorization: float,
    relation_context: RelationContext,
) -> float:
    """Compute a resonance score combining preservation, authorization, and relation context.

    Returns a value in [0.0, 1.0].
    """
    trust = relation_context.trust
    context_affinity = relation_context.context_affinity
    relation_factor = (trust + context_affinity) / 2.0
    return (preservation * 0.5 + authorization * 0.3 + relation_factor * 0.2)
