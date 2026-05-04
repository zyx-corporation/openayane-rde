"""Rollback manager (Phase 3)."""

from __future__ import annotations

from pathlib import Path

from openayane_rde.core.models import ExecutionTaskContract
from openayane_rde.runtime.rollback import RollbackManager


def test_file_snapshot_and_rollback(tmp_path: Path) -> None:
    f = tmp_path / "w.txt"
    f.write_text("one", encoding="utf-8")
    c = ExecutionTaskContract(
        source_tool_call_id="t",
        agent_id="a",
        action_type="write",
        tool_name="w",
        target_resources=["w.txt"],
        rollback_strategy="file_snapshot",
    )
    mgr = RollbackManager(tmp_path)
    plan = mgr.create_plan(c)
    assert plan.validated
    f.write_text("two", encoding="utf-8")
    res = mgr.execute_rollback(plan)
    assert res.status == "completed"
    assert "w.txt" in res.restored_resources or f.read_text() == "one"


def test_none_strategy_not_possible(tmp_path: Path) -> None:
    c = ExecutionTaskContract(
        source_tool_call_id="t",
        agent_id="a",
        action_type="write",
        tool_name="w",
        target_resources=[],
        rollback_strategy="none",
    )
    mgr = RollbackManager(tmp_path)
    plan = mgr.create_plan(c)
    res = mgr.execute_rollback(plan)
    assert res.status == "not_possible"
