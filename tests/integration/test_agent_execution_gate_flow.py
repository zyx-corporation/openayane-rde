"""Integration: tool call → gate → runtime (Phase 3)."""

from __future__ import annotations

from pathlib import Path

from openayane_rde.agent.execution_gate import enforce_execution_decision, evaluate_before_execution
from openayane_rde.core.models import ToolCallRequest, ToolExecutionResult
from openayane_rde.core.time import now_utc
from openayane_rde.policy.execution_rules import ExecutionPolicyConfig
from openayane_rde.relation.sqlite_store import SQLiteRelationStore
from openayane_rde.review.workflow import HumanReviewWorkflow
from openayane_rde.runtime.safe_execution import SafeExecutionRuntime


def test_gate_to_sqlite_event(tmp_path: Path) -> None:
    db = tmp_path / "db.sqlite3"
    store = SQLiteRelationStore(db)
    store.initialize()
    tc = ToolCallRequest(
        tool_call_id="tc1",
        agent_id="agent",
        tool_name="read_file",
        action_name="invoke",
        arguments={"path": "hello.txt"},
        created_at=now_utc(),
    )
    gate, contract = evaluate_before_execution(
        tc,
        store,
        ExecutionPolicyConfig(),
        subject_id="agent",
        object_id="ws",
    )
    wf = HumanReviewWorkflow(store)
    rt = SafeExecutionRuntime(tmp_path)
    (tmp_path / "hello.txt").write_text("x", encoding="utf-8")
    out = enforce_execution_decision(gate, rt, wf, tool_call=tc, contract=contract)
    assert isinstance(out, ToolExecutionResult)
    assert out.status == "completed"
    store.append_execution_event(
        gate,
        agent_id=tc.agent_id,
        tool_name=tc.tool_name,
        tool_call_id=tc.tool_call_id,
        action_type=contract.action_type,
    )
