"""Phase 2 semantic delta extraction from structural diff."""

from __future__ import annotations

from openayane_rde.contract.builder import build_contract
from openayane_rde.core.models import StructuralDiff, Violation
from openayane_rde.semantic.delta_engine import estimate_semantic_delta


def test_json_schema_violation_populates_constraints() -> None:
    contract = build_contract(mode="preservation", requested_action="x", protected_elements=[])
    diff = StructuralDiff(
        contract_id=contract.contract_id,  # type: ignore[union-attr]
        domain="json",
        schema_violations=[
            Violation(
                path="/x",
                violation_type="missing",
                description="missing required",
                risk_hint="high",
            )
        ],
    )
    delta = estimate_semantic_delta(diff, contract)  # type: ignore[arg-type]
    assert delta.semantic_mode == "structural_baseline"
    assert delta.is_stub is True
    assert "/x" in delta.changed_constraints
    assert delta.changed_safety_conditions
