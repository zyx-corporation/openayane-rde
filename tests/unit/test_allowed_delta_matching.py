"""allowed_delta_m / forbidden_delta_m matching."""

from __future__ import annotations

from openayane_rde.contract.builder import build_contract
from openayane_rde.core.models import DiffNode, SemanticDelta, StructuralDiff
from openayane_rde.rde.authorization import match_allowed_delta


def test_forbidden_keyword_routes_to_forbidden_matches() -> None:
    contract = build_contract(
        mode="preservation",
        requested_action="Edit.",
        forbidden_delta_m=["function signature change"],
        allowed_delta_m=["error handling"],
        protected_elements=[],
    )
    assert hasattr(contract, "contract_id")
    diff = StructuralDiff(
        contract_id=contract.contract_id,  # type: ignore[union-attr]
        domain="python",
        changed_nodes=[
            DiffNode(
                path="/fn",
                kind="function",
                before="def f(): pass",
                after="def f(x): pass",
                description="function signature change occurred",
                risk_hint="high",
            )
        ],
    )
    sem = SemanticDelta(contract_id=contract.contract_id)  # type: ignore[arg-type]
    m = match_allowed_delta(diff, sem, contract)  # type: ignore[arg-type]
    assert m.forbidden_matches


def test_allowed_keyword_increases_match_score() -> None:
    contract = build_contract(
        mode="preservation",
        requested_action="Edit.",
        allowed_delta_m=["sentence restructuring"],
        protected_elements=[],
    )
    diff = StructuralDiff(
        contract_id=contract.contract_id,  # type: ignore[union-attr]
        domain="markdown",
        changed_nodes=[
            DiffNode(
                path="/p",
                kind="paragraph",
                before="a",
                after="b",
                description="sentence restructuring for clarity",
                risk_hint="low",
            )
        ],
    )
    sem = SemanticDelta(contract_id=contract.contract_id)  # type: ignore[arg-type]
    m = match_allowed_delta(diff, sem, contract)  # type: ignore[arg-type]
    assert m.match_score >= 0.99
