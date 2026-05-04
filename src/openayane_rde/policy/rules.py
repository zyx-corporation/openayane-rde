"""Default policy rules for Phase 1 Policy Bridge.

Mapping from RDE classification to policy action, using review_policy from TaskContract
or falling back to hard-coded defaults.
"""

from __future__ import annotations

from openayane_rde.core.models import (
    PolicyActionKind,
    RDEClassification,
    RDEResult,
    TaskContract,
)

# Default mapping when review_policy is not consulted.
_DEFAULT_POLICY_MAP: dict[RDEClassification, PolicyActionKind] = {
    "preserved": "approve",
    "authorized_deviation": "approve_with_notes",
    "benign_incidental_drift": "approve_with_notes",
    "suspicious_drift": "human_review",
    "critical_corruption": "halt",
    "creative_deviation": "approve_with_notes",
}

_REVIEW_POLICY_ACTION_MAP: dict[str, PolicyActionKind] = {
    "auto_approve": "approve",
    "approve_with_note": "approve_with_notes",
    "human_review": "human_review",
    "request_revision": "request_revision",
    "halt": "halt",
    "rollback": "rollback",
}


def decide_action(
    rde_result: RDEResult,
    contract: TaskContract,
) -> PolicyActionKind:
    """Determine policy action from RDEResult and TaskContract review_policy.

    Review policy from the contract takes precedence over defaults.
    critical_corruption always maps to halt regardless of review_policy.
    """
    classification = rde_result.classification

    if classification == "critical_corruption":
        return "halt"

    review = contract.review_policy

    if classification == "preserved":
        return _REVIEW_POLICY_ACTION_MAP.get(review.preserved, "human_review")
    if classification == "authorized_deviation":
        return _REVIEW_POLICY_ACTION_MAP.get(review.authorized_deviation, "human_review")
    if classification == "benign_incidental_drift":
        return _REVIEW_POLICY_ACTION_MAP.get(review.benign_incidental_drift, "human_review")
    if classification == "suspicious_drift":
        return _REVIEW_POLICY_ACTION_MAP.get(review.suspicious_drift, "human_review")
    if classification == "creative_deviation":
        return _REVIEW_POLICY_ACTION_MAP.get(review.authorized_deviation, "human_review")
    return _DEFAULT_POLICY_MAP.get(classification, "human_review")
