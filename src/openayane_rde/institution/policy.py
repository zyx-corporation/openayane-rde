"""Deterministic rule / reviewer matching helpers for the Institution Bridge (Phase 4).

Pure functions — no I/O. Intended for `DeterministicInstitutionBridge` and regression tests.
"""

from __future__ import annotations

from openayane_rde.core.models import (
    ExecutionActionType,
    ExternalSideEffectKind,
    RiskLevel,
)
from openayane_rde.institution.models import InstitutionRule, ReviewerAuthority

_RISK_ORDER: dict[RiskLevel, int] = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}


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
