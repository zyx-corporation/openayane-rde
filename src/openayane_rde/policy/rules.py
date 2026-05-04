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
        rp = review.preserved
    elif classification == "authorized_deviation":
        rp = review.authorized_deviation
    elif classification == "benign_incidental_drift":
        rp = review.benign_incidental_drift
    elif classification == "suspicious_drift":
        rp = review.suspicious_drift
    elif classification == "creative_deviation":
        rp = review.authorized_deviation
    else:
        return _DEFAULT_POLICY_MAP.get(classification, "human_review")

    return _REVIEW_POLICY_ACTION_MAP.get(rp, "human_review")
