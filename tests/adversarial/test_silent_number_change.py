"""Adversarial tests: silent number change detection."""

from __future__ import annotations

from openayane_rde.contract.builder import build_contract
from openayane_rde.core.models import GeneratorOutput, ModelInfo, SelfReport
from openayane_rde.diff.markdown_diff import MarkdownDiff
from openayane_rde.policy.bridge import decide_policy
from openayane_rde.rde.core import evaluate_rde
from openayane_rde.semantic.stub import semantic_delta_stub


def run_eval(contract: object, original: str, generated: str, unchanged: list[str]) -> tuple:
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
    return rde_result, policy


def test_silent_threshold_change() -> None:
    """Number silently changed from 0.85 to 0.60."""
    orig = "The detection threshold is 0.85."
    gen = "The detection threshold is 0.60."
    contract = build_contract(
        mode="preservation",
        requested_action="Improve readability.",
        protected_elements=["numbers"],
        allowed_delta_m=["sentence restructuring"],
        forbidden_delta_m=["numeric change"],
    )

    rde_result, policy = run_eval(contract, orig, gen, unchanged=["numbers"])

    assert rde_result.classification in ("suspicious_drift", "critical_corruption")
    assert policy.action in ("human_review", "halt")


def test_silent_count_change() -> None:
    """Count silently changed from 100 to 99."""
    orig = "The dataset contains 100 samples."
    gen = "The dataset contains 99 samples."
    contract = build_contract(
        mode="preservation",
        requested_action="Reformat section.",
        protected_elements=["numbers"],
        forbidden_delta_m=["numeric change"],
    )

    rde_result, _ = run_eval(contract, orig, gen, unchanged=[])

    assert rde_result.classification in ("suspicious_drift", "critical_corruption")
    assert len(rde_result.violated_constraints) >= 1 or len(rde_result.suspicious_elements) >= 1


def test_number_unchanged_no_false_positive() -> None:
    """No number change - should not raise false alarm."""
    text = "The threshold is 0.85 and the count is 42."
    contract = build_contract(
        mode="preservation",
        requested_action="Improve readability.",
        protected_elements=["numbers"],
    )

    rde_result, _ = run_eval(contract, text, text, unchanged=["numbers"])

    assert rde_result.classification == "preserved"
