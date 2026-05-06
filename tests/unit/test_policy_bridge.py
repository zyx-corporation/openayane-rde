"""Unit tests for Policy Bridge (synthetic RDEResult → PolicyDecision only).

Does not prove RDE classification correctness by itself; see
[`docs/63_openayane_rde_testing_policy.md`](../../docs/63_openayane_rde_testing_policy.md) §3.
"""

from __future__ import annotations

from openayane_rde.contract.builder import build_contract
from openayane_rde.core.models import PolicyDecision, RDEResult
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


# ---------------------------------------------------------------------------
# preserved -> approve
# ---------------------------------------------------------------------------


def test_preserved_low_risk_approve() -> None:
    contract = make_contract()
    rde_result = make_rde_result("preserved", "low", "approve", contract.contract_id)  # type: ignore[union-attr]
    decision: PolicyDecision = decide_policy(rde_result, contract)  # type: ignore[arg-type]

    assert decision.action == "approve"
    assert decision.contract_id == contract.contract_id  # type: ignore[union-attr]
    assert decision.rde_result_id == rde_result.result_id


# ---------------------------------------------------------------------------
# authorized_deviation -> approve_with_notes
# ---------------------------------------------------------------------------


def test_authorized_deviation_approve_with_notes() -> None:
    contract = make_contract()
    rde_result = make_rde_result(
        "authorized_deviation", "low", "approve_with_notes", contract.contract_id  # type: ignore[union-attr]
    )
    decision = decide_policy(rde_result, contract)  # type: ignore[arg-type]

    assert decision.action == "approve_with_notes"


# ---------------------------------------------------------------------------
# suspicious_drift -> human_review
# ---------------------------------------------------------------------------


def test_suspicious_drift_human_review() -> None:
    contract = make_contract()
    rde_result = make_rde_result(
        "suspicious_drift", "high", "human_review", contract.contract_id  # type: ignore[union-attr]
    )
    decision = decide_policy(rde_result, contract)  # type: ignore[arg-type]

    assert decision.action == "human_review"


# ---------------------------------------------------------------------------
# critical_corruption -> halt (always)
# ---------------------------------------------------------------------------


def test_critical_corruption_always_halts() -> None:
    contract = make_contract()
    rde_result = make_rde_result(
        "critical_corruption", "critical", "halt", contract.contract_id  # type: ignore[union-attr]
    )
    decision = decide_policy(rde_result, contract)  # type: ignore[arg-type]

    assert decision.action == "halt"


def test_critical_corruption_cannot_auto_apply() -> None:
    contract = build_contract(
        mode="preservation",
        requested_action="Test.",
        protected_elements=["claims"],
        review_policy=build_contract(  # type: ignore[arg-type]
            mode="preservation",
            requested_action="x",
        ).review_policy,  # type: ignore[union-attr]
    )
    rde_result = make_rde_result(
        "critical_corruption", "critical", "halt", contract.contract_id  # type: ignore[union-attr]
    )
    decision = decide_policy(rde_result, contract)  # type: ignore[arg-type]

    assert decision.action == "halt"
    assert "halt" in decision.rationale.lower() or "critical" in decision.rationale.lower()


# ---------------------------------------------------------------------------
# rationale contains key information
# ---------------------------------------------------------------------------


def test_rationale_contains_classification() -> None:
    contract = make_contract()
    rde_result = make_rde_result("preserved", "low", "approve", contract.contract_id)  # type: ignore[union-attr]
    decision = decide_policy(rde_result, contract)  # type: ignore[arg-type]

    assert "preserved" in decision.rationale
