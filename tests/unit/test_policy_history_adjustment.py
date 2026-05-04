"""Regression tests for RelationContext-based policy history adjustments."""

from __future__ import annotations

from openayane_rde.contract.builder import build_contract
from openayane_rde.core.models import PolicyDecision, RDEResult, RelationContext
from openayane_rde.policy.bridge import decide_policy


def make_contract(**kwargs: object) -> object:
    defaults = dict(
        mode="preservation",
        requested_action="Test.",
        protected_elements=["claims"],
    )
    defaults.update(kwargs)
    return build_contract(**defaults)  # type: ignore[arg-type]


def make_rde_result(
    classification: str,
    risk_level: str = "low",
    required_action: str = "approve",
    contract_id: str = "tc_test",
) -> RDEResult:
    return RDEResult(
        contract_id=contract_id,
        classification=classification,  # type: ignore[arg-type]
        resonance_score=0.8,
        preservation_score=0.9,
        authorization_score=0.9,
        risk_level=risk_level,  # type: ignore[arg-type]
        violated_constraints=[],
        suspicious_elements=[],
        required_action=required_action,  # type: ignore[arg-type]
        explanation="Test.",
    )


def test_history_adjust_low_generator_reliability_elevates_approve_to_human_review() -> None:
    contract = make_contract()
    cid = contract.contract_id  # type: ignore[union-attr]
    rde = make_rde_result("preserved", "low", "approve", cid)
    rc = RelationContext(
        subject_id="s",
        object_id="o",
        generator_reliability_score=0.25,
    )
    decision: PolicyDecision = decide_policy(rde, contract, rc)  # type: ignore[arg-type]

    assert decision.action == "human_review"
    assert "History adjustment" in decision.rationale
    assert "generator_reliability_score" in decision.rationale


def test_history_adjust_review_threshold_elevates_approve_only() -> None:
    contract = make_contract()
    cid = contract.contract_id  # type: ignore[union-attr]
    rde = make_rde_result("preserved", "low", "approve", cid)
    rc = RelationContext(
        subject_id="s",
        object_id="o",
        generator_reliability_score=1.0,
        review_threshold_adjustment=0.55,
    )
    decision = decide_policy(rde, contract, rc)  # type: ignore[arg-type]

    assert decision.action == "human_review"
    assert "History adjustment" in decision.rationale
    assert "review_threshold_adjustment" in decision.rationale


def test_history_adjust_high_threshold_elevates_approve_with_notes_to_human_review() -> None:
    contract = make_contract()
    cid = contract.contract_id  # type: ignore[union-attr]
    rde = make_rde_result("authorized_deviation", "low", "approve_with_notes", cid)
    rc = RelationContext(
        subject_id="s",
        object_id="o",
        generator_reliability_score=1.0,
        review_threshold_adjustment=0.75,
    )
    decision = decide_policy(rde, contract, rc)  # type: ignore[arg-type]

    assert decision.action == "human_review"
    assert "History adjustment" in decision.rationale
    assert "approve_with_notes" in decision.rationale.lower()


def test_history_adjust_document_fragility_elevates_to_human_review() -> None:
    contract = make_contract()
    cid = contract.contract_id  # type: ignore[union-attr]
    rde = make_rde_result("authorized_deviation", "low", "approve_with_notes", cid)
    rc = RelationContext(
        subject_id="s",
        object_id="o",
        generator_reliability_score=1.0,
        review_threshold_adjustment=0.0,
        document_fragility_score=0.75,
    )
    decision = decide_policy(rde, contract, rc)  # type: ignore[arg-type]

    assert decision.action == "human_review"
    assert "History adjustment" in decision.rationale
    assert "document_fragility_score" in decision.rationale
