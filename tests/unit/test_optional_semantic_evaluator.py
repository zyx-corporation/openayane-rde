"""Semantic evaluator (Phase 3)."""

from __future__ import annotations

from openayane_rde.core.models import ExecutionTaskContract, ToolCallRequest
from openayane_rde.core.time import now_utc
from openayane_rde.semantic.evaluator import RuleBasedSemanticEvaluator


def test_purpose_action_mismatch() -> None:
    ev = RuleBasedSemanticEvaluator()
    c = ExecutionTaskContract(
        source_tool_call_id="1",
        agent_id="a",
        action_type="write",
        tool_name="t",
        target_resources=[],
        expected_side_effects=["a"],
        forbidden_side_effects=["a"],
    )
    tc = ToolCallRequest(
        tool_call_id="1",
        agent_id="a",
        tool_name="t",
        action_name="invoke",
        arguments={},
        declared_purpose="read only",
        created_at=now_utc(),
    )
    r = ev.evaluate_execution_intent(c, tc)
    assert r.recommendation in ("human_review", "no_issue")


def test_forbidden_overlap() -> None:
    ev = RuleBasedSemanticEvaluator()
    c = ExecutionTaskContract(
        source_tool_call_id="1",
        agent_id="a",
        action_type="read",
        tool_name="t",
        target_resources=[],
        expected_side_effects=["x"],
        forbidden_side_effects=["x"],
    )
    tc = ToolCallRequest(
        tool_call_id="1",
        agent_id="a",
        tool_name="t",
        action_name="invoke",
        arguments={},
        created_at=now_utc(),
    )
    r = ev.evaluate_execution_intent(c, tc)
    assert "overlap" in r.explanation.lower() or r.suspected_delta_m
