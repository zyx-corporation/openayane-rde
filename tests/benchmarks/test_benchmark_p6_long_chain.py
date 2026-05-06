"""Phase 6 long-chain benchmark fixtures (cumulative baseline comparison)."""

from __future__ import annotations

from pathlib import Path

import pytest

from openayane_rde.diff.markdown_diff import MarkdownDiff
from openayane_rde.policy.bridge import decide_policy
from openayane_rde.rde.core import evaluate_rde
from openayane_rde.semantic.stub import semantic_delta_stub

from tests.golden import test_golden as golden

REPO_ROOT = Path(__file__).resolve().parents[2]
LONG_CHAIN_ROOT = (
    REPO_ROOT
    / "benchmarks"
    / "long_chain_document_corruption"
    / "safety_framework_cumulative"
)

_STEPS = ["step_01", "step_02", "step_03"]


def _run_cumulative_step(step: str) -> tuple[str, str]:
    root = LONG_CHAIN_ROOT
    contract = golden.load_contract(root)
    original = (root / "original.md").read_text()
    step_dir = root / step
    modified = (step_dir / "modified.md").read_text()
    go = golden.make_go(contract.contract_id, modified, self_report=None)
    diff = MarkdownDiff().diff(original, modified, contract, go)
    semantic = semantic_delta_stub(diff, contract)
    rde_result = evaluate_rde(
        contract=contract,
        generator_output=go,
        structural_diff=diff,
        semantic_delta=semantic,
    )
    policy_decision = decide_policy(rde_result, contract)
    return rde_result.classification, policy_decision.action


@pytest.mark.parametrize("step", _STEPS, ids=_STEPS)
def test_p6_long_chain_safety_framework_step(step: str) -> None:
    root = LONG_CHAIN_ROOT
    expected = golden.load_expected(root / step)
    classification, action = _run_cumulative_step(step)
    assert classification == expected["classification"], (
        f"{step}: expected classification {expected['classification']!r}, got {classification!r}"
    )
    assert action == expected["required_action"], (
        f"{step}: expected policy action {expected['required_action']!r}, got {action!r}"
    )
