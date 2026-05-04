"""PostExecutionDiff → Phase 1 RDE connector (production readiness Wave B)."""

from __future__ import annotations

from openayane_rde.core.models import PostExecutionDiff
from openayane_rde.runtime.post_execution import run_phase1_evaluation_from_post_execution_diff
from tests.unit.test_phase1_flow import make_contract, make_go


def test_post_execution_diff_wires_phase1_post_structural() -> None:
    text = "# Title\n\nBody and [ref](https://example.com)."
    contract = make_contract()
    go = make_go(contract.contract_id, text)  # type: ignore[union-attr]
    ped = PostExecutionDiff(contract_id=contract.contract_id)

    result = run_phase1_evaluation_from_post_execution_diff(
        ped,
        text,
        go,
        contract,  # type: ignore[arg-type]
        domain="markdown",
    )

    assert result.rde_result.evaluation_kind == "post_structural"
    assert result.rde_result.evidence_basis == ["structural_diff", "semantic_delta"]
    assert result.structural_diff.contract_id == contract.contract_id  # type: ignore[union-attr]


def test_post_execution_diff_adds_observed_side_effects_basis() -> None:
    text = "# A\n\nb"
    contract = make_contract()
    go = make_go(contract.contract_id, text)  # type: ignore[union-attr]
    ped = PostExecutionDiff(
        contract_id=contract.contract_id,
        unexpected_side_effects=["extra file touched"],
    )
    result = run_phase1_evaluation_from_post_execution_diff(
        ped,
        text,
        go,
        contract,  # type: ignore[arg-type]
        domain="markdown",
    )
    assert "observed_side_effects" in result.rde_result.evidence_basis
    assert "structural_diff" in result.rde_result.evidence_basis
