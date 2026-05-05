"""Unit tests for Phase 4 institution skeleton models (Issues #27–#29)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from openayane_rde.institution import (
    ApprovalChain,
    ApprovalStep,
    AuthorityRef,
    EvidenceHandoff,
    HaltProvenance,
    InstitutionalDecision,
    InstitutionRule,
    ReviewerAuthority,
)


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


def test_evidence_handoff_preserves_audit_and_basis() -> None:
    h = EvidenceHandoff(
        handoff_id="h1",
        contract_id="tc_1",
        tool_call_id="tc_1",
        audit_event_ids=["ae_1", "ae_2"],
        evidence_basis=["structural_diff", "human_review_decision"],
        explanation="Phase 3 evidence bundle for bridge.",
        created_at=_dt(),
    )
    h2 = EvidenceHandoff.model_validate_json(h.model_dump_json())
    assert h2.audit_event_ids == ["ae_1", "ae_2"]
    assert "structural_diff" in h2.evidence_basis


def test_institutional_decision_kinds_and_round_trip() -> None:
    d = InstitutionalDecision(
        institutional_decision_id="id_1",
        handoff_id="h1",
        decision="require_higher_authority",
        rationale="Reviewer lacks minimum authority for irreversible side effect.",
        created_at=_dt(),
    )
    d2 = InstitutionalDecision.model_validate_json(d.model_dump_json())
    assert d2.decision == "require_higher_authority"
    assert d2.risk_accepted is False


def test_institutional_decision_invalid_kind_rejected() -> None:
    with pytest.raises(ValidationError):
        InstitutionalDecision.model_validate(
            {
                "institutional_decision_id": "id_1",
                "handoff_id": "h1",
                "decision": "not_a_decision",
                "rationale": "x",
                "created_at": _dt(),
            }
        )


def test_halt_provenance_policy_vs_rde_distinct_in_json() -> None:
    policy = HaltProvenance(
        halt_kind="policy_halt",
        policy_rule_id="pol_1",
        explanation="Blocked before semantic evaluation.",
        evidence_basis=["tool_risk_rule"],
    )
    rde = HaltProvenance(
        halt_kind="rde_halt",
        rde_result_id="rde_9",
        explanation="Structural drift unacceptable.",
        evidence_basis=["structural_diff"],
    )
    p2 = HaltProvenance.model_validate_json(policy.model_dump_json())
    r2 = HaltProvenance.model_validate_json(rde.model_dump_json())
    assert p2.halt_kind == "policy_halt"
    assert p2.policy_rule_id == "pol_1"
    assert r2.halt_kind == "rde_halt"
    assert r2.rde_result_id == "rde_9"


def test_halt_provenance_invalid_kind_rejected() -> None:
    with pytest.raises(ValidationError):
        HaltProvenance.model_validate(
            {
                "halt_kind": "unknown_halt",
                "explanation": "x",
            }
        )


def test_approval_chain_round_trip() -> None:
    chain = ApprovalChain(
        chain_id="dual_1",
        name="Two-step",
        steps=[
            ApprovalStep(order=0, role_id="maintainer", required_approvals=1),
            ApprovalStep(order=1, role_id="security", required_approvals=1),
        ],
    )
    c2 = ApprovalChain.model_validate_json(chain.model_dump_json())
    assert c2.chain_id == "dual_1"
    assert len(c2.steps) == 2
    assert c2.steps[1].role_id == "security"


def test_evidence_handoff_rollback_fields_round_trip() -> None:
    h = EvidenceHandoff(
        handoff_id="h_rb",
        contract_id="c1",
        tool_call_id="t1",
        rollback_plan_id="rbp_1",
        rollback_result_id="rbr_1",
        audit_event_ids=["ae1"],
        evidence_basis=["rollback_result"],
        explanation="x",
        created_at=_dt(),
    )
    h2 = EvidenceHandoff.model_validate_json(h.model_dump_json())
    assert h2.rollback_plan_id == "rbp_1"
    assert h2.rollback_result_id == "rbr_1"
