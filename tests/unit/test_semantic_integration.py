"""Optional semantic evaluator integration seam (Phase 3)."""

from __future__ import annotations

from openayane_rde.core.models import (
    ExecutionTaskContract,
    PostExecutionDiff,
    SemanticEvaluationResult,
    ToolCallRequest,
    ToolExecutionResult,
)
from openayane_rde.core.time import now_utc
from openayane_rde.semantic.evaluator import RuleBasedSemanticEvaluator
from openayane_rde.semantic.integration import (
    optional_evaluate_execution_intent,
    optional_evaluate_post_execution,
)


def test_optional_evaluator_absent_returns_none() -> None:
    c = ExecutionTaskContract(
        source_tool_call_id="1",
        agent_id="a",
        action_type="read",
        tool_name="t",
        target_resources=[],
    )
    tc = ToolCallRequest(
        tool_call_id="1",
        agent_id="a",
        tool_name="t",
        action_name="invoke",
        arguments={},
        created_at=now_utc(),
    )
    assert optional_evaluate_execution_intent(None, c, tc) is None
    r = ToolExecutionResult(
        contract_id="c", tool_call_id="1", status="completed"
    )
    d = PostExecutionDiff(contract_id="c")
    assert optional_evaluate_post_execution(None, c, r, d) is None


def test_optional_evaluator_invokes_rule_based() -> None:
    ev = RuleBasedSemanticEvaluator()
    c = ExecutionTaskContract(
        source_tool_call_id="1",
        agent_id="a",
        action_type="read",
        tool_name="t",
        target_resources=[],
    )
    tc = ToolCallRequest(
        tool_call_id="1",
        agent_id="a",
        tool_name="t",
        action_name="invoke",
        arguments={},
        created_at=now_utc(),
    )
    out = optional_evaluate_execution_intent(ev, c, tc)
    assert isinstance(out, SemanticEvaluationResult)
