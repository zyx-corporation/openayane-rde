"""Unit tests for DeterministicInstitutionBridge (Issue #30)."""

from __future__ import annotations

from datetime import UTC, datetime

from openayane_rde.core.models import (
    ExecutionGateDecision,
    ExecutionGateEvaluation,
    ExecutionTaskContract,
    RDEResult,
    RollbackResult,
    ToolCallRisk,
    ToolExecutionResult,
)
from openayane_rde.institution import (
    AuthorityRef,
    DeterministicInstitutionBridge,
    EvidenceHandoff,
    HandoffDecisionInput,
    InstitutionRule,
    ReviewerAuthority,
)


def _dt() -> datetime:
    return datetime(2026, 5, 5, 12, 0, tzinfo=UTC)


def _rule(*, rule_id: str = "rule_net", allows_irreversible: bool = False) -> InstitutionRule:
    return InstitutionRule(
        rule_id=rule_id,
        name="network publish",
        description="test",
        scope=["*"],
        applies_to_action_types=["network"],
        applies_to_side_effects=["publishing"],
        minimum_authority_level="L1",
        evidence_required=[],
        created_at=_dt(),
        allows_irreversible_action=allows_irreversible,
    )


def _ref() -> AuthorityRef:
    return AuthorityRef(
        authority_id="auth_1",
        authority_type="human_reviewer",
        subject_id="u1",
        authority_level="L2",
    )


def _reviewer(*, max_risk: str = "high", can_irrev: bool = False) -> ReviewerAuthority:
    return ReviewerAuthority(
        reviewer_id="rev1",
        authority_refs=[_ref()],
        allowed_action_types=["network"],
        allowed_side_effects=["publishing"],
        max_risk_level=max_risk,  # type: ignore[arg-type]
        can_approve_irreversible=can_irrev,
    )


def _minimal_evaluation(*, audit_event_id: str | None = "ae_gate") -> ExecutionGateEvaluation:
    contract = ExecutionTaskContract(
        contract_id="etc_eval",
        source_tool_call_id="tcl_1",
        agent_id="ag",
        action_type="network",
        tool_name="web",
        external_side_effect_kind="publishing",
    )
    decision = ExecutionGateDecision(
        contract_id="etc_eval",
        policy_action="approve",
        reason="ok",
        risk=ToolCallRisk(risk_level="high", risk_score=0.6),
        audit_event_id=audit_event_id,
    )
    return ExecutionGateEvaluation(decision=decision, contract=contract)


def test_build_handoff_preserves_contract_and_audit_chain() -> None:
    bridge = DeterministicInstitutionBridge()
    ev = _minimal_evaluation()
    h = bridge.build_handoff(
        handoff_id="h_1",
        evaluation=ev,
        explanation="unit test handoff",
        created_at=_dt(),
    )
    assert h.handoff_id == "h_1"
    assert h.contract_id == "etc_eval"
    assert h.tool_call_id == "tcl_1"
    assert "ae_gate" in h.audit_event_ids
    assert h.gate_decision_id == ev.decision.decision_id
    assert h.evidence_basis == ["tool_risk_rule", "execution_contract"]
    assert "[evidence-handoff]" not in h.explanation


def test_build_handoff_uses_rde_evidence_basis_when_present() -> None:
    bridge = DeterministicInstitutionBridge()
    contract = ExecutionTaskContract(
        contract_id="etc_rde",
        source_tool_call_id="tcl_r",
        agent_id="ag",
        action_type="network",
        tool_name="web",
        external_side_effect_kind="publishing",
    )
    rde = RDEResult(
        contract_id="etc_rde",
        classification="preserved",
        risk_level="low",
        required_action="approve",
        explanation="ok",
        evidence_basis=["structural_diff", "semantic_delta"],
    )
    decision = ExecutionGateDecision(
        contract_id="etc_rde",
        policy_action="approve",
        reason="ok",
        risk=ToolCallRisk(risk_level="low", risk_score=0.1),
        rde_result=rde,
        audit_event_id="ae_1",
    )
    ev = ExecutionGateEvaluation(decision=decision, contract=contract)
    h = bridge.build_handoff(
        handoff_id="h_rde",
        evaluation=ev,
        explanation="with rde",
        created_at=_dt(),
    )
    assert h.evidence_basis == ["structural_diff", "semantic_delta"]
    assert h.rde_result_id == rde.result_id


def test_build_handoff_no_audit_appends_gap_note() -> None:
    bridge = DeterministicInstitutionBridge()
    ev = _minimal_evaluation(audit_event_id=None)
    h = bridge.build_handoff(
        handoff_id="h_gap",
        evaluation=ev,
        explanation="synthetic path",
        created_at=_dt(),
    )
    assert h.audit_event_ids == []
    assert "[evidence-handoff]" in h.explanation
    assert h.evidence_basis == ["tool_risk_rule", "execution_contract"]


def test_build_handoff_links_rollback_plan_and_result() -> None:
    bridge = DeterministicInstitutionBridge()
    ev = _minimal_evaluation()
    tex = ToolExecutionResult(
        contract_id="etc_eval",
        tool_call_id="tcl_1",
        status="completed",
        rollback_plan_id="rbp_9",
        audit_event_id="ae_exec",
    )
    rb = RollbackResult(
        rollback_plan_id="rbp_9",
        status="completed",
        audit_event_id="ae_rb",
    )
    h = bridge.build_handoff(
        handoff_id="h_rb",
        evaluation=ev,
        execution_result=tex,
        rollback_result=rb,
        explanation="rollback path",
        created_at=_dt(),
    )
    assert h.rollback_plan_id == "rbp_9"
    assert h.rollback_result_id == rb.rollback_result_id
    assert "ae_gate" in h.audit_event_ids
    assert "ae_exec" in h.audit_event_ids
    assert "ae_rb" in h.audit_event_ids


def test_decide_accept_reversible() -> None:
    bridge = DeterministicInstitutionBridge()
    h = EvidenceHandoff(
        handoff_id="h1",
        contract_id="c1",
        tool_call_id="t1",
        audit_event_ids=["ae1"],
        evidence_basis=["structural_diff"],
        explanation="ok",
        created_at=_dt(),
    )
    inp = HandoffDecisionInput(
        action_type="network",
        side_effect="publishing",
        risk_level="high",
        reversibility=False,
    )
    d = bridge.decide(h, [_rule()], _reviewer(), decision_input=inp)
    assert d.decision == "accept"
    assert d.rule_id == "rule_net"
    assert d.handoff_id == "h1"
    assert d.audit_event_id == "ae1"


def test_decide_require_more_evidence_no_audit_no_basis() -> None:
    bridge = DeterministicInstitutionBridge()
    h = EvidenceHandoff(
        handoff_id="h1",
        contract_id="c1",
        tool_call_id="t1",
        audit_event_ids=[],
        evidence_basis=[],
        explanation="gap",
        created_at=_dt(),
    )
    inp = HandoffDecisionInput("network", "publishing", "low", False)
    d = bridge.decide(h, [_rule()], _reviewer(), decision_input=inp)
    assert d.decision == "require_more_evidence"


def test_decide_require_more_evidence_unknown_reversibility() -> None:
    bridge = DeterministicInstitutionBridge()
    h = EvidenceHandoff(
        handoff_id="h1",
        contract_id="c1",
        tool_call_id="t1",
        audit_event_ids=["ae1"],
        evidence_basis=["tool_risk_rule"],
        explanation="ok",
        created_at=_dt(),
    )
    inp = HandoffDecisionInput("network", "publishing", "low", None)
    d = bridge.decide(h, [_rule()], _reviewer(), decision_input=inp)
    assert d.decision == "require_more_evidence"


def test_decide_require_higher_authority_insufficient_reviewer_risk() -> None:
    bridge = DeterministicInstitutionBridge()
    h = EvidenceHandoff(
        handoff_id="h1",
        contract_id="c1",
        tool_call_id="t1",
        audit_event_ids=["ae1"],
        evidence_basis=["execution_contract"],
        explanation="ok",
        created_at=_dt(),
    )
    inp = HandoffDecisionInput("network", "publishing", "critical", False)
    d = bridge.decide(h, [_rule()], _reviewer(max_risk="medium"), decision_input=inp)
    assert d.decision == "require_higher_authority"


def test_decide_halt_institutionally_irreversible_rule_forbids() -> None:
    bridge = DeterministicInstitutionBridge()
    h = EvidenceHandoff(
        handoff_id="h1",
        contract_id="c1",
        tool_call_id="t1",
        audit_event_ids=["ae1"],
        evidence_basis=["human_review_decision"],
        explanation="irrev",
        created_at=_dt(),
    )
    inp = HandoffDecisionInput("network", "publishing", "high", True)
    d = bridge.decide(
        h,
        [_rule(allows_irreversible=False)],
        _reviewer(can_irrev=True),
        decision_input=inp,
    )
    assert d.decision == "halt_institutionally"


def test_decide_require_higher_when_review_present_but_no_reviewer_record() -> None:
    bridge = DeterministicInstitutionBridge()
    h = EvidenceHandoff(
        handoff_id="h1",
        contract_id="c1",
        tool_call_id="t1",
        review_decision_id="rd_1",
        audit_event_ids=["ae1"],
        evidence_basis=["human_review_decision"],
        explanation="reviewed",
        created_at=_dt(),
    )
    inp = HandoffDecisionInput("network", "publishing", "high", False)
    d = bridge.decide(h, [_rule()], None, decision_input=inp)
    assert d.decision == "require_higher_authority"


def test_decide_require_more_evidence_no_matching_rule() -> None:
    bridge = DeterministicInstitutionBridge()
    h = EvidenceHandoff(
        handoff_id="h1",
        contract_id="c1",
        tool_call_id="t1",
        audit_event_ids=["ae1"],
        evidence_basis=["structural_diff"],
        explanation="ok",
        created_at=_dt(),
    )
    inp = HandoffDecisionInput("execute", "notification", "low", False)
    d = bridge.decide(h, [_rule()], _reviewer(), decision_input=inp)
    assert d.decision == "require_more_evidence"


def test_decide_accepts_irreversible_when_rule_and_reviewer_allow() -> None:
    """Boundary: irreversible path reaches accept when rule and ReviewerAuthority permit."""

    bridge = DeterministicInstitutionBridge()
    h = EvidenceHandoff(
        handoff_id="h1",
        contract_id="c1",
        tool_call_id="t1",
        audit_event_ids=["ae1"],
        evidence_basis=["human_review_decision"],
        explanation="irrev allowed",
        created_at=_dt(),
    )
    inp = HandoffDecisionInput("network", "publishing", "high", True)
    d = bridge.decide(
        h,
        [_rule(allows_irreversible=True)],
        _reviewer(can_irrev=True),
        decision_input=inp,
    )
    assert d.decision == "accept"
    assert d.irreversible_accepted is True
    assert d.rule_id == "rule_net"
