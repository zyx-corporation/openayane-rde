"""Adversarial tests: generated output removes required JSON field silently.

Phase 1 acceptance criteria (phase1_implementation_plan.md §6.3):
  - generated output removes required JSON field
"""

from __future__ import annotations

import json

from openayane_rde.contract.builder import build_contract
from openayane_rde.core.models import GeneratorOutput, ModelInfo, SelfReport
from openayane_rde.diff.json_diff import JsonDiff
from openayane_rde.policy.bridge import decide_policy
from openayane_rde.rde.core import evaluate_rde
from openayane_rde.semantic.stub import semantic_delta_stub


def make_contract(required_fields: list[str] | None = None) -> object:
    return build_contract(
        mode="preservation",
        requested_action="Update description field only.",
        protected_elements=["schema_keys", "required_fields"],
        allowed_delta_m=["description update"],
        forbidden_delta_m=["required field deletion", "key deletion"],
        metadata={"required_fields": required_fields or []},
    )


def run_eval(
    contract: object,
    original: str,
    generated: str,
    unchanged: list[str],
    required_fields: list[str] | None = None,
) -> tuple:
    go = GeneratorOutput(
        contract_id=contract.contract_id,  # type: ignore[union-attr]
        output_type="full_text",
        payload=generated,
        self_report=SelfReport(unchanged_elements=unchanged),
        model_info=ModelInfo(provider="mock", model="adversarial-test"),
    )
    engine = JsonDiff(required_fields=required_fields or [])
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


# ---------------------------------------------------------------------------
# required field deleted, self_report says nothing changed
# ---------------------------------------------------------------------------


def test_required_field_deleted_silently() -> None:
    """Generator removes a required field and self-reports no change."""
    orig = json.dumps({"name": "alice", "version": "1.0", "status": "active"})
    gen = json.dumps({"name": "alice", "version": "1.0"})
    contract = make_contract(required_fields=["name", "version", "status"])

    rde_result, policy, diff = run_eval(
        contract, orig, gen,
        unchanged=["schema keys", "required fields"],
        required_fields=["name", "version", "status"],
    )

    assert len(diff.schema_violations) >= 1
    violation_types = [v.violation_type for v in diff.schema_violations]
    assert any("required_field" in vt for vt in violation_types)

    assert rde_result.classification == "critical_corruption"
    assert policy.action == "halt"


def test_required_field_deleted_self_report_mismatch_recorded() -> None:
    """Mismatch between self-report and actual diff is recorded."""
    orig = json.dumps({"id": "001", "type": "record", "payload": "data"})
    gen = json.dumps({"id": "001", "payload": "data"})
    contract = make_contract(required_fields=["id", "type", "payload"])

    rde_result, policy, diff = run_eval(
        contract, orig, gen,
        unchanged=["schema keys"],
        required_fields=["id", "type", "payload"],
    )

    assert len(diff.self_report_mismatches) >= 1
    assert rde_result.classification == "critical_corruption"
    assert policy.action == "halt"


def test_multiple_required_fields_deleted() -> None:
    """Generator removes multiple required fields simultaneously."""
    orig = json.dumps({"a": 1, "b": 2, "c": 3, "d": 4})
    gen = json.dumps({"a": 1})
    contract = make_contract(required_fields=["a", "b", "c", "d"])

    rde_result, policy, diff = run_eval(
        contract, orig, gen,
        unchanged=[],
        required_fields=["a", "b", "c", "d"],
    )

    violations = diff.schema_violations
    assert len(violations) >= 3

    assert rde_result.classification == "critical_corruption"
    assert policy.action == "halt"


def test_no_required_field_deleted_no_violation() -> None:
    """All required fields present: no violation, no false positive."""
    orig = json.dumps({"name": "alice", "version": "1.0", "status": "active"})
    gen = json.dumps({"name": "alice", "version": "1.0", "status": "active", "extra": "bonus"})
    contract = make_contract(required_fields=["name", "version", "status"])

    rde_result, policy, diff = run_eval(
        contract, orig, gen,
        unchanged=[],
        required_fields=["name", "version", "status"],
    )

    assert diff.schema_violations == []
    assert rde_result.classification != "critical_corruption"
