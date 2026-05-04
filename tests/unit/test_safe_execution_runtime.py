"""Safe execution runtime (Phase 3)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from openayane_rde.agent.tool_contract import build_execution_task_contract
from openayane_rde.core.models import ToolCallRequest
from openayane_rde.core.time import now_utc
from openayane_rde.runtime.safe_execution import SafeExecutionRuntime


def test_dry_run_write_no_file_change(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    f.write_text("orig", encoding="utf-8")
    tc = ToolCallRequest(
        tool_call_id="1",
        agent_id="a",
        tool_name="write",
        action_name="invoke",
        arguments={"path": "a.txt", "content": "new"},
        target_resources=["a.txt"],
        created_at=now_utc(),
    )
    c = build_execution_task_contract(tc)
    c = c.model_copy(
        update={
            "max_runtime_ms": 100,
            "max_output_bytes": 1000,
        }
    )
    rt = SafeExecutionRuntime(tmp_path)
    r = rt.execute(c, tc, dry_run=True)
    assert r.status == "dry_run_completed"
    assert f.read_text() == "orig"


def test_network_blocked() -> None:
    from openayane_rde.core.models import ExecutionTaskContract
    from openayane_rde.core.time import now_utc as nu

    c = ExecutionTaskContract(
        source_tool_call_id="1",
        agent_id="a",
        action_type="network",
        tool_name="http",
        target_resources=[],
        network_allowed=False,
    )
    tc = ToolCallRequest(
        tool_call_id="1",
        agent_id="a",
        tool_name="http",
        action_name="get",
        arguments={},
        created_at=nu(),
    )
    rt = SafeExecutionRuntime(Path("."))
    r = rt.execute(c, tc)
    assert r.status == "blocked"


def test_path_traversal_dotdot_blocked(tmp_path: Path) -> None:
    ws = tmp_path / "workspace"
    ws.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    tc = ToolCallRequest(
        tool_call_id="1",
        agent_id="a",
        tool_name="read",
        action_name="invoke",
        arguments={"path": "../outside.txt"},
        target_resources=["../outside.txt"],
        created_at=now_utc(),
    )
    c = build_execution_task_contract(tc)
    rt = SafeExecutionRuntime(ws)
    r = rt.execute(c, tc)
    assert r.status == "blocked"
    assert r.error_message == "path_outside_workspace"


@pytest.mark.skipif(sys.platform == "win32", reason="symlink escape test uses POSIX symlinks")
def test_symlink_outside_workspace_blocked(tmp_path: Path) -> None:
    outside = tmp_path / "outside_target.txt"
    outside.write_text("leak", encoding="utf-8")
    ws = tmp_path / "workspace"
    ws.mkdir()
    link = ws / "via_link.txt"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation not available")
    tc = ToolCallRequest(
        tool_call_id="1",
        agent_id="a",
        tool_name="read",
        action_name="invoke",
        arguments={"path": "via_link.txt"},
        target_resources=["via_link.txt"],
        created_at=now_utc(),
    )
    c = build_execution_task_contract(tc)
    rt = SafeExecutionRuntime(ws)
    r = rt.execute(c, tc)
    assert r.status == "blocked"
    assert r.error_message == "path_outside_workspace"
