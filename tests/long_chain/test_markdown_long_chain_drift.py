"""Long-chain drift accumulation (Phase 2 acceptance-style)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from openayane_rde import run_phase1_evaluation
from openayane_rde.contract.builder import build_contract
from openayane_rde.core.models import GeneratorOutput, ModelInfo, RelationContext, SelfReport
from openayane_rde.relation.store import JSONRelationStore
from openayane_rde.relation.update import update_relation_from_evaluation_result


def test_markdown_numeric_drift_chain_accumulates_review_threshold(tmp_path: Path) -> None:
    store_path = tmp_path / "relation.json"
    store = JSONRelationStore(store_path)
    rc = RelationContext(subject_id="gpt", object_id="paper.md")

    contract = build_contract(
        mode="preservation",
        requested_action="Polish wording only.",
        allowed_delta_m=["sentence restructuring"],
        forbidden_delta_m=["numeric change"],
        protected_elements=["numbers"],
    )

    text = "The threshold is 0.95 for acceptance."
    current = text

    with tempfile.TemporaryDirectory() as audit_dir:
        log_path = Path(audit_dir) / "audit.jsonl"

        for i in range(20):
            current = current.replace("0.95", f"{0.94 - i * 0.001:.3f}", 1)
            go = GeneratorOutput(
                contract_id=contract.contract_id,  # type: ignore[union-attr]
                output_type="full_text",
                payload=current,
                self_report=SelfReport(unchanged_elements=["numbers"]),
                model_info=ModelInfo(provider="mock", model="long-chain"),
            )
            result = run_phase1_evaluation(
                original=text,
                generator_output=go,
                task_contract=contract,  # type: ignore[arg-type]
                domain="markdown",
                relation_context=rc,
                audit_log_path=log_path,
            )
            summary = update_relation_from_evaluation_result(result, store=store)
            assert summary.context.trust <= 1.0
            rc = summary.context

    final = store.get("gpt", "paper.md")
    assert final is not None
    assert final.review_threshold_adjustment >= 0.0
    assert final.interaction_count == 20
    assert len(final.drift_patterns) >= 1
