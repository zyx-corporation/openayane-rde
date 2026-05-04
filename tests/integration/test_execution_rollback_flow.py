"""Integration: write → snapshot → mutate → rollback (Phase 3)."""

from __future__ import annotations

from pathlib import Path

from openayane_rde.agent.tool_contract import build_execution_task_contract
from openayane_rde.core.models import ToolCallRequest
from openayane_rde.core.time import now_utc
from openayane_rde.runtime.rollback import RollbackManager
from openayane_rde.runtime.safe_execution import SafeExecutionRuntime


def test_write_snapshot_rollback(tmp_path: Path) -> None:
    f = tmp_path / "data.txt"
    f.write_text("before", encoding="utf-8")
    tc = ToolCallRequest(
        tool_call_id="1",
        agent_id="a",
        tool_name="write",
        action_name="invoke",
        arguments={"path": "data.txt", "content": "after"},
        created_at=now_utc(),
    )
    c = build_execution_task_contract(tc)
    c = c.model_copy(update={"rollback_strategy": "file_snapshot"})
    mgr = RollbackManager(tmp_path)
    plan = mgr.create_plan(c)
    rt = SafeExecutionRuntime(tmp_path)
    rt.execute(c, tc, dry_run=False)
    assert f.read_text() == "after"
    res = mgr.execute_rollback(plan)
    assert res.status == "completed"
    assert f.read_text() == "before"
