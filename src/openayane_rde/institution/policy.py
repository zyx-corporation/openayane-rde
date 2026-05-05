"""Deterministic rule / reviewer matching helpers for the Institution Bridge (Phase 4).

Pure functions — no I/O. Shared by ``DeterministicInstitutionBridge`` and regression tests.
"""

from __future__ import annotations

from dataclasses import dataclass

from openayane_rde.core.models import (
    ExecutionActionType,
    ExternalSideEffectKind,
    RiskLevel,
)
from openayane_rde.institution.models import (
    InstitutionalDecisionKind,
    InstitutionRule,
    ReviewerAuthority,
)

_RISK_ORDER: dict[RiskLevel, int] = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}


@dataclass(frozen=True, slots=True)
class HandoffDecisionInput:
    """Phase 3–derived facts for rule matching (not stored on ``EvidenceHandoff``)."""

    action_type: ExecutionActionType
    side_effect: ExternalSideEffectKind
    risk_level: RiskLevel
    """True = irreversible, False = reversible, None = unknown (conservative)."""
    reversibility: bool | None = None


def reviewer_covers_action(
    ra: ReviewerAuthority,
    *,
    action_type: ExecutionActionType,
    side_effect: ExternalSideEffectKind,
    action_risk: RiskLevel,
) -> bool:
    """Whether ``ra`` declares bounds that cover the action (structural check only)."""

    if action_type not in ra.allowed_action_types:
        return False
    if side_effect not in ra.allowed_side_effects:
        return False
    return _RISK_ORDER[ra.max_risk_level] >= _RISK_ORDER[action_risk]


def first_matching_rule(
    rules: list[InstitutionRule],
    *,
    action_type: ExecutionActionType,
    side_effect: ExternalSideEffectKind,
) -> InstitutionRule | None:
    """First rule that applies to both action type and side effect (list order = determinism)."""

    for rule in rules:
        if action_type in rule.applies_to_action_types and side_effect in rule.applies_to_side_effects:
            return rule
    return None


def check_irreversible_paths(
    rule: InstitutionRule,
    inp: HandoffDecisionInput,
    ra: ReviewerAuthority | None,
) -> InstitutionalDecisionKind | None:
    """Irreversible vs rule / reviewer flags. ``None`` = no early outcome."""

    if inp.reversibility is not True:
        return None
    if not rule.allows_irreversible_action:
        return "halt_institutionally"
    if ra is None:
        return "require_higher_authority"
    if not ra.can_approve_irreversible:
        return "require_higher_authority"
    return None


def check_structural_cover_escalation(
    ra: ReviewerAuthority | None,
    inp: HandoffDecisionInput,
) -> InstitutionalDecisionKind | None:
    """Structural authority bounds. ``None`` = pass (including ``ra is None`` for reversible paths)."""

    if ra is None:
        return None
    if not reviewer_covers_action(
        ra,
        action_type=inp.action_type,
        side_effect=inp.side_effect,
        action_risk=inp.risk_level,
    ):
        return "require_higher_authority"
    return None


def decision_kind_for_reviewer_and_rule(
    ra: ReviewerAuthority,
    rule: InstitutionRule,
    inp: HandoffDecisionInput,
) -> InstitutionalDecisionKind:
    """Outcome when a single ``InstitutionRule`` applies and a ``ReviewerAuthority`` is in scope.

    Ordering matches ``DeterministicInstitutionBridge.decide`` (irreversible checks before
    structural cover). Used by Issue #31 regression tests.
    """

    if inp.reversibility is None:
        return "require_more_evidence"
    early = check_irreversible_paths(rule, inp, ra)
    if early is not None:
        return early
    cov = check_structural_cover_escalation(ra, inp)
    if cov is not None:
        return cov
    return "accept"
