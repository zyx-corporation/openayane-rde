"""Rollback manager (Phase 3)."""

from __future__ import annotations

from pathlib import Path

from openayane_rde.core.models import ExecutionTaskContract, ToolExecutionResult
from openayane_rde.runtime.rollback import (
    RollbackManager,
    should_offer_rollback_for_execution,
)


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


def test_execute_rollback_with_audit(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    f.write_text("one", encoding="utf-8")
    c = ExecutionTaskContract(
        source_tool_call_id="t",
        agent_id="a",
        action_type="write",
        tool_name="w",
        target_resources=["a.txt"],
        rollback_strategy="file_snapshot",
    )
    mgr = RollbackManager(tmp_path)
    plan = mgr.create_plan(c)
    f.write_text("two", encoding="utf-8")
    log = tmp_path / "audit.jsonl"
    res = mgr.execute_rollback_with_audit(
        plan,
        audit_log_path=log,
        trigger_reason="test recovery",
    )
    assert res.status == "completed"
    from openayane_rde.audit.log import load_events

    evs = load_events(log)
    assert len(evs) == 1
    assert evs[0].action == "rollback_completed"
    assert evs[0].explanation == "test recovery"


def test_should_offer_rollback_for_failed_execution() -> None:
    r = ToolExecutionResult(
        contract_id="c",
        tool_call_id="t",
        status="failed",
    )
    assert should_offer_rollback_for_execution(r) is True
    assert should_offer_rollback_for_execution(
        ToolExecutionResult(contract_id="c", tool_call_id="t", status="completed")
    ) is False
    assert should_offer_rollback_for_execution(
        ToolExecutionResult(contract_id="c", tool_call_id="t", status="completed"),
        gate_risk_level="high",
    ) is True


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
