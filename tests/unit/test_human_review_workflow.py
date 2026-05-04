"""Human review workflow (Phase 3)."""

from __future__ import annotations

from openayane_rde.agent.tool_contract import build_execution_task_contract, score_tool_call_risk
from openayane_rde.core.models import ExecutionGateDecision, ReviewDecision, ToolCallRequest
from openayane_rde.core.time import now_utc
from openayane_rde.policy.execution_rules import synthetic_rde_for_tool
from openayane_rde.review.workflow import HumanReviewWorkflow


def _gate(tc: ToolCallRequest) -> ExecutionGateDecision:
    c = build_execution_task_contract(tc)
    risk = score_tool_call_risk(c, raw_arguments=tc.arguments)
    rde = synthetic_rde_for_tool(c.contract_id, risk)
    return ExecutionGateDecision(
        contract_id=c.contract_id,
        policy_action="human_review",
        reason="test",
        risk=risk,
        rde_result=rde,
    )


def test_create_pending_and_reject() -> None:
    wf = HumanReviewWorkflow()
    tc = ToolCallRequest(
        tool_call_id="x",
        agent_id="ag",
        tool_name="w",
        action_name="invoke",
        arguments={"path": "p"},
        created_at=now_utc(),
    )
    c = build_execution_task_contract(tc)
    gate = _gate(tc)
    req = wf.create_request(gate, c, tool_call_id=tc.tool_call_id, agent_id=tc.agent_id)
    assert req.status == "pending"
    assert len(wf.get_pending()) == 1
    dec = ReviewDecision(
        review_request_id=req.review_request_id,
        reviewer_id="u",
        decision="reject",
        reason="nope",
    )
    wf.submit_decision(dec)
    assert wf.get(req.review_request_id) is not None
    assert wf.get(req.review_request_id).status == "rejected"
