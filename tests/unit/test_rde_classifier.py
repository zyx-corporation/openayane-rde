"""Unit tests for RDE Classifier and Core."""

from __future__ import annotations

from openayane_rde.contract.builder import build_contract
from openayane_rde.core.models import (
    GeneratorOutput,
    ModelInfo,
    ProtectedChange,
    RDEResult,
    SelfReport,
    StructuralDiff,
    Violation,
)
from openayane_rde.relation.context_loader import load_neutral_context
from openayane_rde.rde.core import evaluate_rde
from openayane_rde.semantic.stub import semantic_delta_stub


def make_contract(**kwargs: object) -> object:
    defaults = dict(
        mode="preservation",
        requested_action="Test.",
        protected_elements=["claims", "citations", "numbers"],
    )
    defaults.update(kwargs)
    return build_contract(**defaults)  # type: ignore[arg-type]


def make_go(contract_id: str = "tc_test") -> GeneratorOutput:
    return GeneratorOutput(
        contract_id=contract_id,
        output_type="full_text",
        payload="generated",
        self_report=SelfReport(),
        model_info=ModelInfo(provider="mock", model="test"),
    )


def make_empty_diff(contract_id: str = "tc_test") -> StructuralDiff:
    return StructuralDiff(contract_id=contract_id, domain="markdown")


def make_diff_with_protected(
    element: str, change_type: str = "deleted", risk: str = "high"
) -> StructuralDiff:
    return StructuralDiff(
        contract_id="tc_test",
        domain="markdown",
        protected_element_changes=[
            ProtectedChange(
                element=element,
                path=f"/{element}",
                change_type=change_type,  # type: ignore[arg-type]
                description=f"{element} {change_type}.",
                risk_hint=risk,  # type: ignore[arg-type]
            )
        ],
    )


def make_diff_with_critical_violation() -> StructuralDiff:
    return StructuralDiff(
        contract_id="tc_test",
        domain="json",
        schema_violations=[
            Violation(
                path="/status",
                violation_type="required_field_deleted",
                description="Required field deleted.",
                risk_hint="critical",
            )
        ],
    )


# ---------------------------------------------------------------------------
# preserved
# ---------------------------------------------------------------------------


def test_preserved_no_changes() -> None:
    contract = make_contract()
    diff = make_empty_diff(contract.contract_id)  # type: ignore[union-attr]
    semantic = semantic_delta_stub(diff, contract)  # type: ignore[arg-type]
    go = make_go(contract.contract_id)  # type: ignore[union-attr]

    result: RDEResult = evaluate_rde(
        contract=contract,  # type: ignore[arg-type]
        generator_output=go,
        structural_diff=diff,
        semantic_delta=semantic,
        relation_context=load_neutral_context(),
    )

    assert result.classification == "preserved"
    assert result.risk_level == "low"
    assert result.required_action == "approve"


# ---------------------------------------------------------------------------
# authorized_deviation
# ---------------------------------------------------------------------------


def test_authorized_deviation_with_allowed_delta() -> None:
    from openayane_rde.core.models import DiffNode

    contract = build_contract(
        mode="preservation",
        requested_action="Improve style.",
        allowed_delta_m=["sentence restructuring", "redundancy removal"],
        protected_elements=["claims"],
    )

    diff = StructuralDiff(
        contract_id=contract.contract_id,  # type: ignore[union-attr]
        domain="markdown",
        changed_nodes=[
            DiffNode(
                path="/paragraph/1",
                kind="paragraph",
                before="Foo bar baz.",
                after="Bar baz foo.",
                description="Paragraph sentence restructuring applied.",
                risk_hint="low",
            )
        ],
    )

    semantic = semantic_delta_stub(diff, contract)  # type: ignore[arg-type]
    go = make_go(contract.contract_id)  # type: ignore[union-attr]

    result = evaluate_rde(
        contract=contract,  # type: ignore[arg-type]
        generator_output=go,
        structural_diff=diff,
        semantic_delta=semantic,
    )

    assert result.classification == "authorized_deviation"
    assert result.required_action == "approve_with_notes"


# ---------------------------------------------------------------------------
# suspicious_drift
# ---------------------------------------------------------------------------


def test_suspicious_drift_protected_element_changed() -> None:
    contract = make_contract()
    diff = make_diff_with_protected("citations", "deleted", "high")
    semantic = semantic_delta_stub(diff, contract)  # type: ignore[arg-type]
    go = make_go(contract.contract_id)  # type: ignore[union-attr]

    result = evaluate_rde(
        contract=contract,  # type: ignore[arg-type]
        generator_output=go,
        structural_diff=diff,
        semantic_delta=semantic,
    )

    assert result.classification == "suspicious_drift"
    assert result.required_action == "human_review"


# ---------------------------------------------------------------------------
# critical_corruption
# ---------------------------------------------------------------------------


def test_critical_corruption_from_critical_protected_change() -> None:
    contract = make_contract()
    diff = make_diff_with_protected("citations", "deleted", "critical")
    semantic = semantic_delta_stub(diff, contract)  # type: ignore[arg-type]
    go = make_go(contract.contract_id)  # type: ignore[union-attr]

    result = evaluate_rde(
        contract=contract,  # type: ignore[arg-type]
        generator_output=go,
        structural_diff=diff,
        semantic_delta=semantic,
    )

    assert result.classification == "critical_corruption"
    assert result.required_action == "halt"
    assert result.risk_level == "critical"


def test_critical_corruption_from_schema_violation() -> None:
    contract = make_contract(protected_elements=["required_fields"])
    diff = make_diff_with_critical_violation()
    diff = StructuralDiff(
        contract_id=contract.contract_id,  # type: ignore[union-attr]
        domain="json",
        schema_violations=make_diff_with_critical_violation().schema_violations,
    )
    semantic = semantic_delta_stub(diff, contract)  # type: ignore[arg-type]
    go = make_go(contract.contract_id)  # type: ignore[union-attr]

    result = evaluate_rde(
        contract=contract,  # type: ignore[arg-type]
        generator_output=go,
        structural_diff=diff,
        semantic_delta=semantic,
    )

    assert result.classification == "critical_corruption"
    assert result.required_action == "halt"


# ---------------------------------------------------------------------------
# Self-report mismatch raises risk
# ---------------------------------------------------------------------------


def test_self_report_mismatch_raises_risk() -> None:
    from openayane_rde.core.models import SelfReportMismatch

    contract = make_contract()
    diff = StructuralDiff(
        contract_id=contract.contract_id,  # type: ignore[union-attr]
        domain="markdown",
        self_report_mismatches=[
            SelfReportMismatch(
                reported="citations unchanged",
                actual="citation deleted",
                description="Mismatch.",
                risk_hint="high",
            )
        ],
        protected_element_changes=[
            ProtectedChange(
                element="citations",
                path="/citations",
                change_type="deleted",
                description="Citation deleted.",
                risk_hint="high",
            )
        ],
    )
    semantic = semantic_delta_stub(diff, contract)  # type: ignore[arg-type]
    go = make_go(contract.contract_id)  # type: ignore[union-attr]

    result = evaluate_rde(
        contract=contract,  # type: ignore[arg-type]
        generator_output=go,
        structural_diff=diff,
        semantic_delta=semantic,
    )

    assert result.classification in ("suspicious_drift", "critical_corruption")
    assert len(result.suspicious_elements) >= 1
