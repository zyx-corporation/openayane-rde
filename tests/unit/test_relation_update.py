"""Relation layer hooks from Phase1EvaluationResult."""

from __future__ import annotations

from pathlib import Path

from openayane_rde import (
    Phase1EvaluationResult,
    RelationUpdateSummary,
    update_relation_from_evaluation_result,
)
from openayane_rde.contract.builder import build_contract
from openayane_rde.core.models import (
    AuditEvent,
    GeneratorOutput,
    ModelInfo,
    PolicyDecision,
    RelationContext,
    RDEResult,
    SelfReport,
    SemanticDelta,
    StructuralDiff,
    TaskContract,
)
from openayane_rde.relation.store import JSONRelationStore


def _minimal_result(
    *,
    audit: AuditEvent | None,
    relation_context: RelationContext | None,
) -> Phase1EvaluationResult:
    tc = build_contract(
        mode="preservation",
        requested_action="x",
        protected_elements=[],
    )
    assert isinstance(tc, TaskContract)
    go = GeneratorOutput(
        contract_id=tc.contract_id,
        output_type="full_text",
        payload="x",
        self_report=SelfReport(),
        model_info=ModelInfo(provider="mock", model="t"),
    )
    sd = StructuralDiff(contract_id=tc.contract_id, domain="markdown")
    sem = SemanticDelta(contract_id=tc.contract_id)
    rde = RDEResult(
        contract_id=tc.contract_id,
        classification="preserved",
        risk_level="low",
        required_action="approve",
        explanation="t",
    )
    pd = PolicyDecision(
        contract_id=tc.contract_id,
        rde_result_id=rde.result_id,
        action="approve",
        rationale="t",
    )
    return Phase1EvaluationResult(
        task_contract=tc,
        generator_output=go,
        relation_context=relation_context,
        structural_diff=sd,
        semantic_delta=sem,
        rde_result=rde,
        policy_decision=pd,
        audit_event=audit,
    )


def test_update_relation_without_audit_returns_message() -> None:
    rc = RelationContext(subject_id="s", object_id="o")
    result = _minimal_result(audit=None, relation_context=rc)
    summary = update_relation_from_evaluation_result(result)
    assert isinstance(summary, RelationUpdateSummary)
    assert summary.updated is False
    assert summary.context is rc


def test_update_relation_with_audit_no_store_is_in_memory_only() -> None:
    result = _minimal_result(
        audit=AuditEvent(
            actor="rde",
            action="evaluate_rde",
            explanation="e",
        ),
        relation_context=None,
    )
    summary = update_relation_from_evaluation_result(result)
    assert summary.updated is False
    assert "No RelationStore" in summary.message


def test_update_relation_with_store_and_audit_persists(tmp_path: Path) -> None:
    store = JSONRelationStore(tmp_path / "rs.json")
    rc = RelationContext(subject_id="gen", object_id="doc")
    result = _minimal_result(
        audit=AuditEvent(
            actor="rde",
            action="evaluate_rde",
            explanation="e",
        ),
        relation_context=rc,
    )
    summary = update_relation_from_evaluation_result(result, store=store)
    assert summary.updated is True
    assert summary.trust_before is not None
    assert summary.trust_after is not None
    assert store.get("gen", "doc") is not None


def test_update_relation_store_without_audit_option_a(tmp_path: Path) -> None:
    store = JSONRelationStore(tmp_path / "rs.json")
    result = _minimal_result(
        audit=None,
        relation_context=RelationContext(subject_id="a", object_id="b"),
    )
    summary = update_relation_from_evaluation_result(result, store=store)
    assert summary.updated is False
    assert "audit_event" in summary.message.lower()
