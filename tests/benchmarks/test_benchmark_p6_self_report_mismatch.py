"""Phase 6 generator self-report mismatch benchmark."""

from __future__ import annotations

from pathlib import Path

from openayane_rde.diff.markdown_diff import MarkdownDiff
from openayane_rde.semantic.stub import semantic_delta_stub

from tests.golden import test_golden as golden

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = (
    REPO_ROOT / "benchmarks" / "generator_self_report_mismatch" / "silent_delta_claim"
)


def test_p6_self_report_mismatch_silent_delta_claim() -> None:
    expected = golden.load_expected(FIXTURE)
    contract = golden.load_contract(FIXTURE)
    original = (FIXTURE / "original.md").read_text()
    modified = (FIXTURE / "modified.md").read_text()
    self_report = golden.load_self_report(FIXTURE)
    assert self_report is not None

    go = golden.make_go(contract.contract_id, modified, self_report=self_report)
    diff = MarkdownDiff().diff(original, modified, contract, go)
    semantic = semantic_delta_stub(diff, contract)
    rde_result = golden.evaluate_rde(
        contract=contract,
        generator_output=go,
        structural_diff=diff,
        semantic_delta=semantic,
    )

    assert rde_result.classification == expected["classification"], (
        f"expected {expected['classification']!r}, got {rde_result.classification!r}"
    )
    if expected.get("must_have_self_report_mismatches"):
        assert len(diff.self_report_mismatches) >= 1, (
            "expected at least one self_report mismatch row"
        )
    if expected.get("must_have_protected_element_changes"):
        assert len(diff.protected_element_changes) >= 1, (
            "expected at least one protected element change"
        )
