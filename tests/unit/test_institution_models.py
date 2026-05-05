"""Unit tests for Phase 4 institution skeleton models (Issue #27)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from openayane_rde.institution import AuthorityRef, InstitutionRule, ReviewerAuthority


def _dt() -> datetime:
    return datetime(2026, 5, 5, 12, 0, tzinfo=UTC)


def test_institution_rule_round_trip() -> None:
    rule = InstitutionRule(
        rule_id="rule_1",
        name="External publish",
        description="Publishing requires institutional sign-off.",
        scope=["repo:main"],
        applies_to_action_types=["network"],
        applies_to_side_effects=["publishing"],
        minimum_authority_level="L2",
        evidence_required=["human_review_decision"],
        created_at=_dt(),
        requires_human_review=True,
    )
    restored = InstitutionRule.model_validate_json(rule.model_dump_json())
    assert restored.rule_id == "rule_1"
    assert restored.requires_human_review is True


def test_authority_ref_invalid_type_rejected() -> None:
    with pytest.raises(ValidationError):
        AuthorityRef.model_validate(
            {
                "authority_id": "a1",
                "authority_type": "not_a_valid_literal",
                "subject_id": "u1",
                "authority_level": "L1",
            }
        )


def test_reviewer_authority_bounds_and_round_trip() -> None:
    ref = AuthorityRef(
        authority_id="auth_1",
        authority_type="human_reviewer",
        subject_id="reviewer_42",
        authority_level="L2",
    )
    ra = ReviewerAuthority(
        reviewer_id="reviewer_42",
        authority_refs=[ref],
        allowed_action_types=["write", "network"],
        allowed_side_effects=["state_changing_request"],
        max_risk_level="high",
        can_approve_irreversible=False,
    )
    data = ra.model_dump_json()
    ra2 = ReviewerAuthority.model_validate_json(data)
    assert ra2.max_risk_level == "high"
    assert len(ra2.authority_refs) == 1
    assert ra2.authority_refs[0].authority_type == "human_reviewer"


def test_empty_rule_id_rejected() -> None:
    with pytest.raises(ValidationError):
        InstitutionRule(
            rule_id="",
            name="x",
            description="y",
            scope=[],
            applies_to_action_types=[],
            applies_to_side_effects=[],
            minimum_authority_level="L0",
            evidence_required=[],
            created_at=_dt(),
        )
