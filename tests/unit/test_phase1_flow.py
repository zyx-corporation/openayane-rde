"""Integration tests for the Phase 1 runtime flow (run_phase1_evaluation).

Verifies the full evaluation pipeline described in phase1_implementation_plan.md §5:

    structural_diff = run_structural_diff(original, generated_output, task_contract)
    semantic_delta  = semantic_delta_stub(structural_diff)
    rde_result      = evaluate_rde(...)
    policy_decision = decide_policy(rde_result, task_contract)
    audit_event     = write_audit_event(...)
    return policy_decision
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from openayane_rde import run_phase1_evaluation
from openayane_rde.audit.log import load_events
from openayane_rde.contract.builder import build_contract
from openayane_rde.core.models import GeneratorOutput, ModelInfo, SelfReport


def make_contract(**kwargs: object) -> object:
    defaults = dict(
        mode="preservation",
        requested_action="Improve readability.",
        protected_elements=["citations", "numbers", "definitions"],
        allowed_delta_m=["sentence restructuring"],
        forbidden_delta_m=["citation removal", "numeric change"],
    )
    defaults.update(kwargs)
    return build_contract(**defaults)  # type: ignore[arg-type]


def make_go(contract_id: str, payload: str, unchanged: list[str] | None = None) -> GeneratorOutput:
    return GeneratorOutput(
        contract_id=contract_id,
        output_type="full_text",
        payload=payload,
        self_report=SelfReport(unchanged_elements=unchanged or []),
        model_info=ModelInfo(provider="mock", model="integration-test"),
    )


# ---------------------------------------------------------------------------
# Markdown: no change → preserve
# ---------------------------------------------------------------------------


def test_flow_markdown_preserved() -> None:
    text = "# Title\n\nSome content. See [ref](https://example.com). Value is 42."
    contract = make_contract()
    go = make_go(contract.contract_id, text)  # type: ignore[union-attr]

    decision = run_phase1_evaluation(
        original=text,
        generator_output=go,
        task_contract=contract,  # type: ignore[arg-type]
        domain="markdown",
    )

    assert decision.action == "approve"
    assert decision.contract_id == contract.contract_id  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Markdown: citation deleted → critical_corruption → halt
# ---------------------------------------------------------------------------


def test_flow_markdown_citation_deleted_halts() -> None:
    original = "See [Smith 2020](https://example.com) for the method."
    generated = "See the method."
    contract = make_contract()
    go = make_go(contract.contract_id, generated)  # type: ignore[union-attr]

    decision = run_phase1_evaluation(
        original=original,
        generator_output=go,
        task_contract=contract,  # type: ignore[arg-type]
        domain="markdown",
    )

    assert decision.action == "halt"


# ---------------------------------------------------------------------------
# JSON: required field deleted → critical_corruption → halt
# ---------------------------------------------------------------------------


def test_flow_json_required_field_deleted_halts() -> None:
    original = json.dumps({"name": "alice", "version": "1.0", "status": "active"})
    generated = json.dumps({"name": "alice", "version": "1.0"})
    contract = build_contract(
        mode="preservation",
        requested_action="Update description.",
        protected_elements=["required_fields", "schema_keys"],
    )
    go = make_go(contract.contract_id, generated)  # type: ignore[union-attr]

    decision = run_phase1_evaluation(
        original=original,
        generator_output=go,
        task_contract=contract,  # type: ignore[arg-type]
        domain="json",
        required_json_fields=["name", "version", "status"],
    )

    assert decision.action == "halt"


# ---------------------------------------------------------------------------
# Python: function signature changed → suspicious_drift → human_review
# ---------------------------------------------------------------------------


def test_flow_python_signature_changed_human_review() -> None:
    original = "def run(x: int, y: int) -> int:\n    return x + y\n"
    generated = "def run(x: int) -> int:\n    return x\n"
    contract = build_contract(
        mode="refactor",
        requested_action="Add error handling.",
        protected_elements=["function_signatures"],
        allowed_delta_m=["try/except addition"],
    )
    go = make_go(contract.contract_id, generated)  # type: ignore[union-attr]

    decision = run_phase1_evaluation(
        original=original,
        generator_output=go,
        task_contract=contract,  # type: ignore[arg-type]
        domain="python",
    )

    assert decision.action in ("human_review", "halt")


# ---------------------------------------------------------------------------
# Audit log is written when path is provided
# ---------------------------------------------------------------------------


def test_flow_audit_log_written() -> None:
    text = "# Title\n\nContent with [ref](https://example.com) and value 42."
    contract = make_contract()
    go = make_go(contract.contract_id, text)  # type: ignore[union-attr]

    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "audit" / "events.jsonl"

        decision = run_phase1_evaluation(
            original=text,
            generator_output=go,
            task_contract=contract,  # type: ignore[arg-type]
            domain="markdown",
            audit_log_path=log_path,
        )

        assert log_path.exists()
        events = load_events(log_path)
        assert len(events) == 1

        ev = events[0]
        assert ev.task_contract_id == contract.contract_id  # type: ignore[union-attr]
        assert ev.generator_output_id == go.output_id
        assert ev.rde_result_id is not None
        assert ev.policy_decision_id == decision.decision_id
        assert ev.hash_before is not None
        assert ev.hash_after is not None
        assert ev.action == "evaluate_rde"


def test_flow_audit_log_not_written_when_path_is_none() -> None:
    text = "Simple content."
    contract = make_contract()
    go = make_go(contract.contract_id, text)  # type: ignore[union-attr]

    decision = run_phase1_evaluation(
        original=text,
        generator_output=go,
        task_contract=contract,  # type: ignore[arg-type]
        domain="markdown",
        audit_log_path=None,
    )

    assert decision is not None


# ---------------------------------------------------------------------------
# Self-report mismatch is detected and recorded in audit log
# ---------------------------------------------------------------------------


def test_flow_self_report_mismatch_in_audit() -> None:
    original = "The threshold is 0.95. See [ref](https://example.com)."
    generated = "The threshold is 0.70. See the reference."
    contract = make_contract()
    go = make_go(
        contract.contract_id,  # type: ignore[union-attr]
        generated,
        unchanged=["numbers", "citations"],
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "events.jsonl"

        decision = run_phase1_evaluation(
            original=original,
            generator_output=go,
            task_contract=contract,  # type: ignore[arg-type]
            domain="markdown",
            audit_log_path=log_path,
        )

        events = load_events(log_path)
        assert len(events) == 1
        ev = events[0]
        assert ev.payload.get("classification") in (
            "suspicious_drift", "critical_corruption"
        )
        assert decision.action in ("human_review", "halt")
