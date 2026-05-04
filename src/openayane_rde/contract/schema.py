"""Default TaskContract schema helpers."""

from __future__ import annotations

from openayane_rde.core.models import OutputPolicy, ReviewPolicy


def default_output_policy() -> OutputPolicy:
    return OutputPolicy(
        require_patch=True,
        require_change_report=True,
        require_uncertainty_report=True,
    )


def default_review_policy() -> ReviewPolicy:
    return ReviewPolicy(
        preserved="auto_approve",
        authorized_deviation="approve_with_note",
        benign_incidental_drift="approve_with_note",
        suspicious_drift="human_review",
        critical_corruption="halt",
    )
