"""Long-chain drift accumulation (Phase 2 acceptance-style)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from openayane_rde import run_phase1_evaluation
from openayane_rde.contract.builder import build_contract
from openayane_rde.core.models import GeneratorOutput, ModelInfo, RelationContext, SelfReport
from openayane_rde.relation.store import JSONRelationStore
from openayane_rde.relation.update import update_relation_from_evaluation_result


def test_markdown_numeric_drift_chain_baseline_comparison(tmp_path: Path) -> None:
    """Original vs version_n each step (cumulative drift vs fixed baseline)."""

    store = JSONRelationStore(tmp_path / "relation.json")
    rc = RelationContext(subject_id="gpt", object_id="paper.md")

    contract = build_contract(
        mode="preservation",
        requested_action="Polish wording only.",
        allowed_delta_m=["sentence restructuring"],
        forbidden_delta_m=["numeric change"],
        protected_elements=["numbers"],
    )

    original = "The threshold is 0.950 for acceptance."
    val = 0.950

    with tempfile.TemporaryDirectory() as audit_dir:
        log_path = Path(audit_dir) / "audit.jsonl"

        for _ in range(20):
            val -= 0.001
            current = f"The threshold is {val:.3f} for acceptance."
            go = GeneratorOutput(
                contract_id=contract.contract_id,  # type: ignore[union-attr]
                output_type="full_text",
                payload=current,
                self_report=SelfReport(unchanged_elements=["numbers"]),
                model_info=ModelInfo(provider="mock", model="long-chain"),
            )
            result = run_phase1_evaluation(
                original=original,
                generator_output=go,
                task_contract=contract,  # type: ignore[arg-type]
                domain="markdown",
                relation_context=rc,
                audit_log_path=log_path,
            )
            summary = update_relation_from_evaluation_result(result, store=store)
            rc = summary.context

    final = store.get("gpt", "paper.md")
    assert final is not None
    assert final.interaction_count == 20
    assert final.review_threshold_adjustment > 0.0
    assert final.self_report_mismatch_count > 0
    assert final.trust < 0.5
    kinds = [p.kind for p in final.drift_patterns]
    assert any(k in ("number_change", "self_report_mismatch") for k in kinds)


def test_markdown_numeric_drift_chain_stepwise_comparison(tmp_path: Path) -> None:
    """version_{n-1} vs version_n at each step."""

    store = JSONRelationStore(tmp_path / "relation2.json")
    rc = RelationContext(subject_id="gpt", object_id="step.md")

    contract = build_contract(
        mode="preservation",
        requested_action="Polish wording only.",
        allowed_delta_m=["sentence restructuring"],
        forbidden_delta_m=["numeric change"],
        protected_elements=["numbers"],
    )

    prev = "The threshold is 0.950 for acceptance."
    val = 0.950

    with tempfile.TemporaryDirectory() as audit_dir:
        log_path = Path(audit_dir) / "audit.jsonl"

        for _ in range(20):
            val -= 0.001
            current = f"The threshold is {val:.3f} for acceptance."
            go = GeneratorOutput(
                contract_id=contract.contract_id,  # type: ignore[union-attr]
                output_type="full_text",
                payload=current,
                self_report=SelfReport(unchanged_elements=["numbers"]),
                model_info=ModelInfo(provider="mock", model="long-chain-step"),
            )
            result = run_phase1_evaluation(
                original=prev,
                generator_output=go,
                task_contract=contract,  # type: ignore[arg-type]
                domain="markdown",
                relation_context=rc,
                audit_log_path=log_path,
            )
            summary = update_relation_from_evaluation_result(result, store=store)
            rc = summary.context
            prev = current

    final = store.get("gpt", "step.md")
    assert final is not None
    assert final.interaction_count == 20
    assert final.review_threshold_adjustment > 0.0
