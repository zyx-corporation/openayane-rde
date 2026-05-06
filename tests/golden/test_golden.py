"""Golden tests using fixed fixtures.

Each fixture must include:
  original (file or .md/.json/.py)
  modified (file)
  task_contract.json
  expected_rde_result.json

RDE classification vs Policy action: [`docs/63_openayane_rde_testing_policy.md`](../../docs/63_openayane_rde_testing_policy.md) §3.
Assertions use separate messages for classification (RDE) and required_action (policy path).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


from openayane_rde.core.models import (
    GeneratorOutput,
    ModelInfo,
    OutputPolicy,
    ReviewPolicy,
    SelfReport,
    TargetScope,
    TaskContract,
)
from openayane_rde.diff.json_diff import JsonDiff
from openayane_rde.diff.markdown_diff import MarkdownDiff
from openayane_rde.diff.python_ast_diff import PythonAstDiff
from openayane_rde.policy.bridge import decide_policy
from openayane_rde.rde.core import evaluate_rde
from openayane_rde.semantic.stub import semantic_delta_stub

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_contract(fixture_dir: Path) -> TaskContract:
    data: dict[str, Any] = json.loads((fixture_dir / "task_contract.json").read_text())
    return TaskContract(
        contract_id=data["contract_id"],
        mode=data["mode"],
        target_scope=TargetScope(**data["target_scope"]),
        requested_action=data["requested_action"],
        allowed_delta_m=data.get("allowed_delta_m", []),
        forbidden_delta_m=data.get("forbidden_delta_m", []),
        protected_elements=data.get("protected_elements", []),
        output_policy=OutputPolicy(**data["output_policy"]),
        review_policy=ReviewPolicy(**data["review_policy"]),
        relation_context_ref=data.get("relation_context_ref"),
        metadata=data.get("metadata", {}),
    )


def load_expected(fixture_dir: Path) -> dict[str, str]:
    return json.loads((fixture_dir / "expected_rde_result.json").read_text())


def test_expected_rde_result_shape() -> None:
    """All golden fixtures must pin both RDE classification and policy action."""
    for expected_path in FIXTURES_DIR.glob("*/expected_rde_result.json"):
        data = json.loads(expected_path.read_text())
        assert "classification" in data, f"Missing classification: {expected_path}"
        assert "required_action" in data, f"Missing required_action: {expected_path}"


def make_go(
    contract_id: str,
    payload: str,
    self_report: SelfReport | None = None,
) -> GeneratorOutput:
    return GeneratorOutput(
        contract_id=contract_id,
        output_type="full_text",
        payload=payload,
        self_report=self_report or SelfReport(),
        model_info=ModelInfo(provider="mock", model="golden-test"),
    )


def load_self_report(fixture_dir: Path) -> SelfReport | None:
    path = fixture_dir / "self_report.json"
    if not path.exists():
        return None
    data: dict[str, Any] = json.loads(path.read_text())
    return SelfReport(**data)


def run_golden_fixture(
    fixture_dir: Path,
    domain: str,
    original_file: str,
    modified_file: str,
    required_json_fields: list[str] | None = None,
) -> tuple[str, str]:
    """Run evaluation for a fixture, return (actual_classification, actual_action)."""
    contract = load_contract(fixture_dir)
    original = (fixture_dir / original_file).read_text()
    modified = (fixture_dir / modified_file).read_text()
    self_report = load_self_report(fixture_dir)

    go = make_go(contract.contract_id, modified, self_report=self_report)

    if domain == "markdown":
        engine = MarkdownDiff()
    elif domain == "json":
        engine = JsonDiff(required_fields=required_json_fields or [])
    elif domain == "python":
        engine = PythonAstDiff()
    else:
        raise ValueError(f"Unknown domain: {domain}")

    diff = engine.diff(original, modified, contract, go)
    semantic = semantic_delta_stub(diff, contract)
    rde_result = evaluate_rde(
        contract=contract,
        generator_output=go,
        structural_diff=diff,
        semantic_delta=semantic,
    )
    policy_decision = decide_policy(rde_result, contract)

    return rde_result.classification, policy_decision.action


# ---------------------------------------------------------------------------
# markdown_preserved
# ---------------------------------------------------------------------------


def test_golden_markdown_preserved() -> None:
    fixture = FIXTURES_DIR / "markdown_preserved"
    expected = load_expected(fixture)

    classification, action = run_golden_fixture(
        fixture, "markdown", "original.md", "modified.md"
    )

    assert classification == expected["classification"], (
        f"Expected classification {expected['classification']!r}, got {classification!r}"
    )
    assert action == expected["required_action"], (
        f"Expected action {expected['required_action']!r}, got {action!r}"
    )


# ---------------------------------------------------------------------------
# markdown_definition_changed
# ---------------------------------------------------------------------------


def test_golden_markdown_definition_changed() -> None:
    fixture = FIXTURES_DIR / "markdown_definition_changed"
    expected = load_expected(fixture)

    classification, action = run_golden_fixture(
        fixture, "markdown", "original.md", "modified.md"
    )

    assert classification == expected["classification"], (
        f"Expected classification {expected['classification']!r}, got {classification!r}"
    )
    assert action == expected["required_action"], (
        f"Expected action {expected['required_action']!r}, got {action!r}"
    )


# ---------------------------------------------------------------------------
# markdown_citation_deleted
# ---------------------------------------------------------------------------


def test_golden_markdown_citation_deleted() -> None:
    fixture = FIXTURES_DIR / "markdown_citation_deleted"
    expected = load_expected(fixture)

    classification, action = run_golden_fixture(
        fixture, "markdown", "original.md", "modified.md"
    )

    assert classification == expected["classification"], (
        f"Expected classification {expected['classification']!r}, got {classification!r}"
    )
    assert action == expected["required_action"], (
        f"Expected action {expected['required_action']!r}, got {action!r}"
    )


# ---------------------------------------------------------------------------
# json_required_key_deleted
# ---------------------------------------------------------------------------


def test_golden_json_required_key_deleted() -> None:
    fixture = FIXTURES_DIR / "json_required_key_deleted"
    expected = load_expected(fixture)

    contract = load_contract(fixture)
    required_fields: list[str] = contract.metadata.get("required_fields", [])

    classification, action = run_golden_fixture(
        fixture,
        "json",
        "original.json",
        "modified.json",
        required_json_fields=required_fields,
    )

    assert classification == expected["classification"], (
        f"Expected classification {expected['classification']!r}, got {classification!r}"
    )
    assert action == expected["required_action"], (
        f"Expected action {expected['required_action']!r}, got {action!r}"
    )


# ---------------------------------------------------------------------------
# python_signature_changed
# ---------------------------------------------------------------------------


def test_golden_python_signature_changed() -> None:
    fixture = FIXTURES_DIR / "python_signature_changed"
    expected = load_expected(fixture)

    classification, action = run_golden_fixture(
        fixture, "python", "original.py", "modified.py"
    )

    assert classification == expected["classification"], (
        f"Expected classification {expected['classification']!r}, got {classification!r}"
    )
    assert action == expected["required_action"], (
        f"Expected action {expected['required_action']!r}, got {action!r}"
    )


# ---------------------------------------------------------------------------
# self_report_mismatch
# ---------------------------------------------------------------------------


def test_golden_self_report_mismatch() -> None:
    """Generator self-report claims no change but numbers and citation were altered."""
    fixture = FIXTURES_DIR / "self_report_mismatch"
    expected = load_expected(fixture)

    contract = load_contract(fixture)
    original = (fixture / "original.md").read_text()
    modified = (fixture / "modified.md").read_text()
    self_report = load_self_report(fixture)

    go = make_go(contract.contract_id, modified, self_report=self_report)

    engine = MarkdownDiff()
    diff = engine.diff(original, modified, contract, go)

    semantic = semantic_delta_stub(diff, contract)
    rde_result = evaluate_rde(
        contract=contract,
        generator_output=go,
        structural_diff=diff,
        semantic_delta=semantic,
    )
    policy_decision = decide_policy(rde_result, contract)

    assert rde_result.classification == expected["classification"], (
        f"Expected {expected['classification']!r}, got {rde_result.classification!r}"
    )
    assert policy_decision.action == expected["required_action"], (
        f"Expected policy action {expected['required_action']!r}, got {policy_decision.action!r}"
    )
    if expected.get("must_have_self_report_mismatches"):
        assert len(diff.self_report_mismatches) >= 1, (
            "Expected at least one self_report mismatch"
        )
    if expected.get("must_have_protected_element_changes"):
        assert len(diff.protected_element_changes) >= 1, (
            "Expected at least one protected element change"
        )
