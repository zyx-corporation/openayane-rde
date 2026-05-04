"""Adversarial tests: Generator self-report mismatch.

Tests that RDE detects when the Generator's self_report contradicts the actual diff.
"""

from __future__ import annotations

from openayane_rde.contract.builder import build_contract
from openayane_rde.core.models import GeneratorOutput, ModelInfo, SelfReport
from openayane_rde.diff.markdown_diff import MarkdownDiff
from openayane_rde.diff.python_ast_diff import PythonAstDiff
from openayane_rde.rde.core import evaluate_rde
from openayane_rde.semantic.stub import semantic_delta_stub


def make_preservation_contract(**kwargs: object) -> object:
    defaults = dict(
        mode="preservation",
        requested_action="Improve readability.",
        protected_elements=["claims", "citations", "numbers", "definitions"],
    )
    defaults.update(kwargs)
    return build_contract(**defaults)  # type: ignore[arg-type]


def run_eval(contract: object, original: str, generated: str, unchanged: list[str]) -> object:
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
    return evaluate_rde(
        contract=contract,  # type: ignore[arg-type]
        generator_output=go,
        structural_diff=diff,
        semantic_delta=semantic,
    )


# ---------------------------------------------------------------------------
# self_report says citations unchanged but citation removed
# ---------------------------------------------------------------------------


def test_self_report_citation_removed_silently() -> None:
    """Generator claims citations unchanged, but actually removed one."""
    orig = "According to [Smith 2020](https://example.com), the method is valid."
    gen = "According to the literature, the method is valid."
    contract = make_preservation_contract()

    result = run_eval(contract, orig, gen, unchanged=["citations", "claims"])

    assert result.classification in ("suspicious_drift", "critical_corruption"), (
        f"Expected suspicious or critical, got {result.classification}"
    )
    assert len(result.suspicious_elements) >= 1


# ---------------------------------------------------------------------------
# self_report says numbers unchanged but number changed
# ---------------------------------------------------------------------------


def test_self_report_number_changed_silently() -> None:
    """Generator claims numbers unchanged, but a number was changed."""
    orig = "The accuracy is 0.95 on the benchmark."
    gen = "The accuracy is 0.70 on the benchmark."
    contract = make_preservation_contract()

    result = run_eval(contract, orig, gen, unchanged=["numbers", "claims"])

    assert result.classification in ("suspicious_drift", "critical_corruption"), (
        f"Expected suspicious or critical, got {result.classification}"
    )


# ---------------------------------------------------------------------------
# Generator self_report is honest (no mismatch expected)
# ---------------------------------------------------------------------------


def test_honest_self_report_no_mismatch() -> None:
    """Generator accurately reports what changed."""
    orig = "The system is fast."
    gen = "The system is efficient."
    contract = make_preservation_contract(
        allowed_delta_m=["wording improvement"],
        protected_elements=["numbers", "citations"],
    )

    go = GeneratorOutput(
        contract_id=contract.contract_id,  # type: ignore[union-attr]
        output_type="full_text",
        payload=gen,
        self_report=SelfReport(
            changed_elements=["wording"],
            unchanged_elements=["numbers", "citations"],
        ),
        model_info=ModelInfo(provider="mock", model="adversarial-test"),
    )
    engine = MarkdownDiff()
    diff = engine.diff(orig, gen, contract, go)  # type: ignore[arg-type]

    assert diff.self_report_mismatches == []


# ---------------------------------------------------------------------------
# Python: signature changed silently
# ---------------------------------------------------------------------------


def test_python_signature_changed_silently() -> None:
    """Generator changes function signature but reports it as unchanged."""
    orig = "def run(x: int, y: int) -> int:\n    return x + y\n"
    gen = "def run(x: int) -> int:\n    return x\n"
    contract = build_contract(
        mode="refactor",
        requested_action="Add logging.",
        protected_elements=["function_signatures"],
        allowed_delta_m=["logging addition"],
    )

    go = GeneratorOutput(
        contract_id=contract.contract_id,  # type: ignore[union-attr]
        output_type="full_text",
        payload=gen,
        self_report=SelfReport(unchanged_elements=["function signatures"]),
        model_info=ModelInfo(provider="mock", model="adversarial-test"),
    )

    engine = PythonAstDiff()
    diff = engine.diff(orig, gen, contract, go)  # type: ignore[arg-type]
    semantic = semantic_delta_stub(diff, contract)  # type: ignore[arg-type]
    result = evaluate_rde(
        contract=contract,  # type: ignore[arg-type]
        generator_output=go,
        structural_diff=diff,
        semantic_delta=semantic,
    )

    assert result.classification in ("suspicious_drift", "critical_corruption")
    assert len(result.suspicious_elements) >= 1
