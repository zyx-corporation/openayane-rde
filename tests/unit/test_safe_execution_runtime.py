"""Safe execution runtime (Phase 3)."""

from __future__ import annotations

from pathlib import Path

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
