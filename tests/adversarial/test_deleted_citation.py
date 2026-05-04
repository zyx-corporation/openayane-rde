"""Adversarial tests: deleted citation detection.

Tests that citation deletion is always caught, regardless of self-report claims.
"""

from __future__ import annotations

from openayane_rde.contract.builder import build_contract
from openayane_rde.core.models import GeneratorOutput, ModelInfo, SelfReport
from openayane_rde.diff.markdown_diff import MarkdownDiff
from openayane_rde.policy.bridge import decide_policy
from openayane_rde.rde.core import evaluate_rde
from openayane_rde.semantic.stub import semantic_delta_stub


def run_eval(
    contract: object, original: str, generated: str, unchanged: list[str]
) -> tuple:
    go = GeneratorOutput(
        contract_id=contract.contract_id,  # type: ignore[union-attr]
        output_type="full_text",
        payload=generated,
        self_report=SelfReport(unchanged_elements=unchanged),
        model_info=ModelInfo(provider="mock", model="adversarial-test"),
    )
    engine = MarkdownDiff()
    diff = engine.diff(original, generated, contract, go)  # type: ignore[arg-type]
    semantic = semantic_delta_stub(diff, contract)  # type: ignore[arg-type]
    rde_result = evaluate_rde(
        contract=contract,  # type: ignore[arg-type]
        generator_output=go,
        structural_diff=diff,
        semantic_delta=semantic,
    )
    policy = decide_policy(rde_result, contract)  # type: ignore[arg-type]
    return rde_result, policy, diff


def make_preservation_contract(**kwargs: object) -> object:
    defaults = dict(
        mode="preservation",
        requested_action="Improve readability.",
        protected_elements=["citations", "claims"],
    )
    defaults.update(kwargs)
    return build_contract(**defaults)  # type: ignore[arg-type]


def test_citation_deleted_detected() -> None:
    """Link citation deleted from the document."""
    orig = "See [Smith 2020](https://example.com/smith2020) for the proof."
    gen = "See the source for the proof."
    contract = make_preservation_contract()

    rde_result, policy, diff = run_eval(contract, orig, gen, unchanged=[])

    assert len(diff.deleted_nodes) >= 1
    deleted_kinds = [n.kind for n in diff.deleted_nodes]
    assert "citation" in deleted_kinds or "link" in deleted_kinds

    assert rde_result.classification in ("suspicious_drift", "critical_corruption")


def test_numeric_citation_deleted() -> None:
    """Numeric citation [1] deleted."""
    orig = "This is supported by prior work [1]."
    gen = "This is supported by prior work."
    contract = make_preservation_contract()

    rde_result, policy, diff = run_eval(contract, orig, gen, unchanged=[])

    assert rde_result.classification in ("suspicious_drift", "critical_corruption")


def test_citation_deleted_halt_enforced() -> None:
    """Citation deletion in critical mode must produce halt."""
    orig = "Critical safety guarantee from [SafetySpec 2023](https://spec.example.com)."
    gen = "Critical safety guarantee."
    contract = build_contract(
        mode="preservation",
        requested_action="Improve readability.",
        protected_elements=["citations"],
        forbidden_delta_m=["citation removal"],
    )

    rde_result, policy, _ = run_eval(contract, orig, gen, unchanged=["citations"])

    assert rde_result.classification in ("suspicious_drift", "critical_corruption")
    if rde_result.classification == "critical_corruption":
        assert policy.action == "halt"


def test_no_citation_no_false_positive() -> None:
    """Document with no citations: no citation change detected."""
    text = "This is a statement with no references."
    contract = make_preservation_contract()

    rde_result, _, diff = run_eval(contract, text, text, unchanged=[])

    assert rde_result.classification == "preserved"
    assert diff.protected_element_changes == []
