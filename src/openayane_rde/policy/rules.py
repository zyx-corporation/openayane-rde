"""Default policy rules for Phase 1 Policy Bridge.

Mapping from RDE classification to policy action, using review_policy from TaskContract
or falling back to hard-coded defaults.
"""

from __future__ import annotations

from typing import assert_never

from openayane_rde.core.models import (
    PolicyActionKind,
    RDEResult,
    RelationContext,
    TaskContract,
)

_REVIEW_POLICY_ACTION_MAP: dict[str, PolicyActionKind] = {
    "auto_approve": "approve",
    "approve_with_note": "approve_with_notes",
    "human_review": "human_review",
    "request_revision": "request_revision",
    "halt": "halt",
    "rollback": "rollback",
}

HIGH_HISTORY_THRESHOLD_FOR_APPROVE_WITH_NOTES = 0.7


def decide_action(
    rde_result: RDEResult,
    contract: TaskContract,
    relation_context: RelationContext | None = None,
) -> tuple[PolicyActionKind, list[str]]:
    """Determine policy action from RDEResult and TaskContract review_policy.

    Review policy from the contract takes precedence over defaults.
    critical_corruption always maps to halt regardless of review_policy.

    Returns:
        Chosen action and optional audit-facing notes when Relation history
        elevated approve / approve_with_notes to human_review.
    """
    classification = rde_result.classification

    if classification == "critical_corruption":
        return "halt", []

    review = contract.review_policy

    def _adjust_for_history(action: PolicyActionKind) -> tuple[PolicyActionKind, list[str]]:
        notes: list[str] = []
        if relation_context is None:
            return action, notes
        cur = action

        rel = relation_context.generator_reliability_score
        if rel is not None and rel <= 0.3 and cur in ("approve", "approve_with_notes"):
            notes.append(
                "History adjustment: generator_reliability_score <= 0.3; "
                "elevated policy action to human_review."
            )
            cur = "human_review"
        elif (
            cur == "approve"
            and relation_context.review_threshold_adjustment >= 0.5
        ):
            notes.append(
                "History adjustment: review_threshold_adjustment >= 0.5; "
                "elevated approve to human_review."
            )
            cur = "human_review"
        elif (
            cur == "approve_with_notes"
            and relation_context.review_threshold_adjustment
            >= HIGH_HISTORY_THRESHOLD_FOR_APPROVE_WITH_NOTES
        ):
            notes.append(
                "History adjustment: review_threshold_adjustment >= "
                f"{HIGH_HISTORY_THRESHOLD_FOR_APPROVE_WITH_NOTES}; "
                "elevated approve_with_notes to human_review."
            )
            cur = "human_review"
        elif (
            (df := relation_context.document_fragility_score) is not None
            and df >= 0.7
            and cur in ("approve", "approve_with_notes")
        ):
            notes.append(
                "History adjustment: document_fragility_score >= 0.7; "
                "elevated policy action to human_review."
            )
            cur = "human_review"

        return cur, notes

    if classification == "preserved":
        base = _REVIEW_POLICY_ACTION_MAP.get(review.preserved, "human_review")
        return _adjust_for_history(base)
    if classification == "authorized_deviation":
        base = _REVIEW_POLICY_ACTION_MAP.get(review.authorized_deviation, "human_review")
        return _adjust_for_history(base)
    if classification == "benign_incidental_drift":
        base = _REVIEW_POLICY_ACTION_MAP.get(review.benign_incidental_drift, "human_review")
        return _adjust_for_history(base)
    if classification == "suspicious_drift":
        return (
            _REVIEW_POLICY_ACTION_MAP.get(review.suspicious_drift, "human_review"),
            [],
        )
    if classification == "creative_deviation":
        base = _REVIEW_POLICY_ACTION_MAP.get(review.authorized_deviation, "human_review")
        return _adjust_for_history(base)
    assert_never(classification)
