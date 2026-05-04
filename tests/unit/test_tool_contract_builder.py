"""Tool contract builder and risk scoring (Phase 3)."""

from __future__ import annotations

from openayane_rde.agent.tool_contract import (
    build_execution_task_contract,
    score_tool_call_risk,
)
from openayane_rde.core.models import ToolCallRequest
from openayane_rde.core.time import now_utc


def test_read_file_low_risk() -> None:
    tc = ToolCallRequest(
        tool_call_id="1",
        agent_id="a",
        tool_name="read_file",
        action_name="invoke",
        arguments={"path": "/tmp/x"},
        created_at=now_utc(),
    )
    c = build_execution_task_contract(tc)
    assert c.action_type == "read"
    r = score_tool_call_risk(c, raw_arguments=tc.arguments)
    assert r.risk_level == "low"


def test_write_medium_risk(tmp_path) -> None:
    rel = "out.txt"
    (tmp_path / rel).write_text("hi", encoding="utf-8")
    tc = ToolCallRequest(
        tool_call_id="2",
        agent_id="a",
        tool_name="write",
        action_name="invoke",
        arguments={"path": str(tmp_path / rel), "content": "z"},
        created_at=now_utc(),
    )
    c = build_execution_task_contract(tc)
    r = score_tool_call_risk(c, raw_arguments=tc.arguments)
    assert r.risk_level == "medium"


def test_unknown_target_high_risk() -> None:
    tc = ToolCallRequest(
        tool_call_id="3",
        agent_id="a",
        tool_name="write",
        action_name="invoke",
        arguments={"content": "z"},
        created_at=now_utc(),
    )
    c = build_execution_task_contract(tc)
    r = score_tool_call_risk(c)
    assert r.unknown_target is True


def test_secret_critical() -> None:
    tc = ToolCallRequest(
        tool_call_id="4",
        agent_id="a",
        tool_name="read_file",
        action_name="invoke",
        arguments={"path": "/x", "api_key": "secret"},
        created_at=now_utc(),
    )
    c = build_execution_task_contract(tc)
    r = score_tool_call_risk(c, raw_arguments=tc.arguments)
    assert r.risk_level == "critical"

