"""Phase 4: institution hooks on Phase 1 flow and execution gate.

Institution can change the final policy action after RDE; tests should pin **RDE** and **policy**
separately where both matter ([`docs/63_openayane_rde_testing_policy.md`](../../docs/63_openayane_rde_testing_policy.md) §3).
"""

from __future__ import annotations

from datetime import UTC, datetime

from openayane_rde.agent.execution_gate import evaluate_before_execution
from openayane_rde.contract.builder import build_contract
from openayane_rde.core.models import GeneratorOutput, ModelInfo, SelfReport, ToolCallRequest
from openayane_rde.institution.models import InstitutionRule
from openayane_rde.core.time import now_utc
from openayane_rde.institution.rule_registry import InstitutionRuleRegistry
from openayane_rde.policy.execution_rules import ExecutionPolicyConfig
from openayane_rde.relation.store import JSONRelationStore
from openayane_rde.runtime._flow import run_phase1_evaluation


def _dt() -> datetime:
    return datetime(2026, 6, 1, 12, 0, tzinfo=UTC)


def _rule_doc_requires_review() -> InstitutionRule:
    return InstitutionRule(
        rule_id="rule_write_doc",
        name="doc",
        description="d",
        scope=["*"],
        applies_to_action_types=["write"],
        applies_to_side_effects=["none"],
        minimum_authority_level="L1",
        evidence_required=[],
        created_at=_dt(),
        requires_human_review=True,
    )


def _rule_read_requires_review() -> InstitutionRule:
    return InstitutionRule(
        rule_id="rule_read_gate",
        name="read",
        description="d",
        scope=["*"],
        applies_to_action_types=["read"],
        applies_to_side_effects=["none"],
        minimum_authority_level="L1",
        evidence_required=[],
        created_at=_dt(),
        requires_human_review=True,
    )


def _rule_read_rollback_note_only() -> InstitutionRule:
    return InstitutionRule(
        rule_id="rule_read_rb",
        name="read rollback note",
        description="d",
        scope=["*"],
        applies_to_action_types=["read"],
        applies_to_side_effects=["none"],
        minimum_authority_level="L1",
        evidence_required=[],
        created_at=_dt(),
        requires_human_review=False,
        requires_rollback_plan=True,
    )


def test_run_phase1_evaluation_institution_escalates_approve_to_human_review() -> None:
    text = "# Title\n\nSome content. See [ref](https://example.com). Value is 42."
    contract = build_contract(
        mode="preservation",
        requested_action="Improve readability.",
        protected_elements=["citations", "numbers", "definitions"],
        allowed_delta_m=["sentence restructuring"],
        forbidden_delta_m=["citation removal", "numeric change"],
    )
    go = GeneratorOutput(
        contract_id=contract.contract_id,  # type: ignore[union-attr]
        output_type="full_text",
        payload=text,
        self_report=SelfReport(unchanged_elements=[]),
        model_info=ModelInfo(provider="mock", model="t"),
    )
    reg = InstitutionRuleRegistry([_rule_doc_requires_review()])
    result = run_phase1_evaluation(
        original=text,
        generator_output=go,
        task_contract=contract,  # type: ignore[arg-type]
        domain="markdown",
        institution_registry=reg,
        institution_action_type="write",
        institution_side_effect="none",
    )
    assert result.rde_result.classification == "preserved"
    assert result.policy_decision.action == "human_review"
    assert result.policy_decision.institution_rule_id == "rule_write_doc"


def test_evaluate_before_execution_institution_escalates_low_risk_read(tmp_path) -> None:
    store = JSONRelationStore(tmp_path / "rel.json")
    tc = ToolCallRequest(
        tool_call_id="p4_1",
        agent_id="agent",
        tool_name="read_file",
        action_name="invoke",
        arguments={"path": "doc.txt"},
        created_at=now_utc(),
    )
    reg = InstitutionRuleRegistry([_rule_read_requires_review()])
    ev = evaluate_before_execution(
        tc,
        store,
        ExecutionPolicyConfig(),
        subject_id="s",
        object_id="o",
        institution_registry=reg,
    )
    assert ev.decision.policy_action == "human_review"
    assert ev.decision.institution_rule_id == "rule_read_gate"


def test_evaluate_before_execution_rollback_plan_only_keeps_approve(tmp_path) -> None:
    """requires_rollback_plan without requires_human_review: still approve, institution note set."""

    store = JSONRelationStore(tmp_path / "rel.json")
    tc = ToolCallRequest(
        tool_call_id="p4_rb",
        agent_id="agent",
        tool_name="read_file",
        action_name="invoke",
        arguments={"path": "doc.txt"},
        created_at=now_utc(),
    )
    reg = InstitutionRuleRegistry([_rule_read_rollback_note_only()])
    ev = evaluate_before_execution(
        tc,
        store,
        ExecutionPolicyConfig(),
        subject_id="s",
        object_id="o",
        institution_registry=reg,
    )
    assert ev.decision.policy_action == "approve"
    assert ev.decision.institution_rule_id == "rule_read_rb"
    assert ev.decision.institutional_rationale is not None
    assert "rollback" in ev.decision.institutional_rationale.lower()


def test_evaluate_before_execution_pop_critical_fail_halts_when_not_already_halted(
    tmp_path,
) -> None:
    """Critical ToolCallRisk + halt disabled → human_review; failed PoP then forces halt."""

    class BadPop:
        def has_valid_pop(self, subject_id: str) -> bool:
            return False

    store = JSONRelationStore(tmp_path / "rel.json")
    tc = ToolCallRequest(
        tool_call_id="p4_2",
        agent_id="agent",
        tool_name="bash",
        action_name="invoke",
        arguments={"command": "echo", "token": "abc"},
        created_at=now_utc(),
    )
    cfg = ExecutionPolicyConfig(halt_on_critical_risk=False)
    ev = evaluate_before_execution(
        tc,
        store,
        cfg,
        subject_id="s",
        object_id="o",
        pop_verifier=BadPop(),
        pop_subject_id="subj",
    )
    assert ev.decision.policy_action == "halt"
    assert ev.decision.institutional_rationale is not None
