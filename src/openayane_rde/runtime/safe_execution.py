"""Safe Execution Runtime — bounded file/subprocess execution (Phase 3).

Operational boundaries (application sandbox, not OS-level isolation)
---------------------------------------------------------------------
* Paths are confined to ``workspace_root`` using ``resolve()`` + prefix checks; symlink
  escapes that resolve outside the workspace are rejected. This is not TOCTOU-safe.
* Network and ``external_api`` actions are not implemented here; the contract must allow
  them or execution returns ``blocked``.
* Subprocesses run only when ``allow_subprocess_execution`` is true and the argv matches
  ``subprocess_allowlist``. Dangerous argv patterns are rejected even if allowlisted.
* ``contract.max_runtime_ms`` is enforced for **subprocess** execution via
  ``Popen.communicate`` deadlines (terminate + reap on timeout). It does **not** bound
  wall time for in-process read/write/delete simulation (no cancellation of disk I/O).
* Optional ``cancellation_event`` supports cooperative cancellation: checked before
  filesystem side effects and polled during subprocess completion. In-flight subprocess
  cancellation kills the child process; there is no CPU/memory cgroup enforcement.

Failure modes are conservative: blocked paths return ``blocked``; timeouts return
``timed_out``; cancellation returns ``failed`` with ``error_message="cancelled"``.
"""

from __future__ import annotations

import re
import shlex
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from openayane_rde.core.models import (
    ExecutionTaskContract,
    RollbackPlan,
    ToolCallRequest,
    ToolExecutionResult,
)
from openayane_rde.core.time import now_utc


def _is_under_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _cancelled_execution_result(
    contract: ExecutionTaskContract,
    tool_call: ToolCallRequest,
    *,
    started: datetime,
    rollback_plan: RollbackPlan | None,
) -> ToolExecutionResult:
    return ToolExecutionResult(
        contract_id=contract.contract_id,
        tool_call_id=tool_call.tool_call_id,
        status="failed",
        stderr="Execution cancelled before completion.",
        started_at=started,
        completed_at=now_utc(),
        error_message="cancelled",
        rollback_plan_id=rollback_plan.rollback_plan_id if rollback_plan else None,
    )


def _truncate(s: str, max_bytes: int | None) -> str:
    if max_bytes is None or max_bytes <= 0:
        return s
    b = s.encode("utf-8")
    if len(b) <= max_bytes:
        return s
    return b[:max_bytes].decode("utf-8", errors="replace") + "\n[truncated]"


class SafeExecutionRuntime:
    """Application-level safe execution (not a full OS sandbox).

    Use ``cancellation_event`` for cooperative shutdown; subprocess timeouts use
    ``ExecutionTaskContract.max_runtime_ms`` (see module docstring).
    """

    def __init__(
        self,
        workspace_root: str | Path,
        *,
        allow_subprocess_execution: bool = False,
        subprocess_allowlist: dict[str, list[str]] | None = None,
    ) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.allow_subprocess_execution = allow_subprocess_execution
        self.subprocess_allowlist = subprocess_allowlist or {}

    def execute(
        self,
        contract: ExecutionTaskContract,
        tool_call: ToolCallRequest,
        rollback_plan: RollbackPlan | None = None,
        *,
        dry_run: bool = False,
        cancellation_event: threading.Event | None = None,
    ) -> ToolExecutionResult:
        """Execute or simulate a tool call within workspace and policy limits."""

        started = now_utc()
        max_out = contract.max_output_bytes or 64_000

        if cancellation_event is not None and cancellation_event.is_set():
            return _cancelled_execution_result(
                contract, tool_call, started=started, rollback_plan=rollback_plan
            )

        for p in contract.protected_resources:
            for t in contract.target_resources:
                if t and p and (t == p or t.startswith(p)):
                    if contract.action_type in ("write", "delete", "execute"):
                        return ToolExecutionResult(
                            contract_id=contract.contract_id,
                            tool_call_id=tool_call.tool_call_id,
                            status="blocked",
                            stderr="Blocked: protected resource.",
                            started_at=started,
                            completed_at=now_utc(),
                            error_message="protected_resource",
                        )

        if contract.action_type in ("network", "external_api") and not contract.network_allowed:
            return ToolExecutionResult(
                contract_id=contract.contract_id,
                tool_call_id=tool_call.tool_call_id,
                status="blocked",
                stderr="Network action not allowed by contract.",
                started_at=started,
                completed_at=now_utc(),
                error_message="network_disallowed",
            )

        if contract.action_type == "execute":
            return self._execute_subprocess(
                contract,
                tool_call,
                rollback_plan,
                dry_run=dry_run,
                cancellation_event=cancellation_event,
            )

        # File-oriented simulation for read/write/delete
        target = contract.target_resources[0] if contract.target_resources else ""
        path = (self.workspace_root / target.lstrip("/")).resolve() if target else self.workspace_root
        if target and not _is_under_root(path, self.workspace_root):
            return ToolExecutionResult(
                contract_id=contract.contract_id,
                tool_call_id=tool_call.tool_call_id,
                status="blocked",
                stderr="Path escapes workspace.",
                started_at=started,
                completed_at=now_utc(),
                error_message="path_outside_workspace",
            )

        if contract.action_type == "read":
            if cancellation_event is not None and cancellation_event.is_set():
                return _cancelled_execution_result(
                    contract, tool_call, started=started, rollback_plan=rollback_plan
                )
            if not path.is_file():
                return ToolExecutionResult(
                    contract_id=contract.contract_id,
                    tool_call_id=tool_call.tool_call_id,
                    status="failed",
                    stderr=f"Not a file: {path}",
                    started_at=started,
                    completed_at=now_utc(),
                )
            content = path.read_text(encoding="utf-8", errors="replace")
            content = _truncate(content, max_out)
            return ToolExecutionResult(
                contract_id=contract.contract_id,
                tool_call_id=tool_call.tool_call_id,
                status="completed",
                stdout=content,
                changed_resources=[],
                started_at=started,
                completed_at=now_utc(),
            )

        if contract.action_type == "write":
            if cancellation_event is not None and cancellation_event.is_set():
                return _cancelled_execution_result(
                    contract, tool_call, started=started, rollback_plan=rollback_plan
                )
            if dry_run:
                return ToolExecutionResult(
                    contract_id=contract.contract_id,
                    tool_call_id=tool_call.tool_call_id,
                    status="dry_run_completed",
                    stdout=f"Would write to {path} (dry-run; no bytes written).",
                    changed_resources=[],
                    started_at=started,
                    completed_at=now_utc(),
                    rollback_plan_id=rollback_plan.rollback_plan_id if rollback_plan else None,
                )
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = tool_call.arguments.get("content") or tool_call.arguments.get("text") or ""
            if not isinstance(payload, str):
                payload = str(payload)
            path.write_text(_truncate(payload, max_out), encoding="utf-8")
            return ToolExecutionResult(
                contract_id=contract.contract_id,
                tool_call_id=tool_call.tool_call_id,
                status="completed",
                changed_resources=[str(path.relative_to(self.workspace_root))],
                started_at=started,
                completed_at=now_utc(),
                rollback_plan_id=rollback_plan.rollback_plan_id if rollback_plan else None,
            )

        if contract.action_type == "delete":
            if cancellation_event is not None and cancellation_event.is_set():
                return _cancelled_execution_result(
                    contract, tool_call, started=started, rollback_plan=rollback_plan
                )
            if dry_run:
                return ToolExecutionResult(
                    contract_id=contract.contract_id,
                    tool_call_id=tool_call.tool_call_id,
                    status="dry_run_completed",
                    stdout=f"Would delete {path} (dry-run).",
                    changed_resources=[],
                    started_at=started,
                    completed_at=now_utc(),
                )
            if path.is_file():
                path.unlink()
            return ToolExecutionResult(
                contract_id=contract.contract_id,
                tool_call_id=tool_call.tool_call_id,
                status="completed",
                changed_resources=[str(path.relative_to(self.workspace_root))],
                started_at=started,
                completed_at=now_utc(),
            )

        return ToolExecutionResult(
            contract_id=contract.contract_id,
            tool_call_id=tool_call.tool_call_id,
            status="not_executed",
            stderr="Unsupported action for minimal runtime.",
            started_at=started,
            completed_at=now_utc(),
        )

    def _communicate_subprocess(
        self,
        proc: subprocess.Popen[Any],
        *,
        deadline_s: float,
        cancellation_event: threading.Event | None,
        max_out: int,
    ) -> tuple[str, str, Literal["ok", "timeout", "cancelled"]]:
        end = time.monotonic() + deadline_s
        while True:
            if cancellation_event is not None and cancellation_event.is_set():
                if proc.poll() is None:
                    proc.kill()
                out, err = proc.communicate(timeout=30)
                return (
                    _truncate(out or "", max_out),
                    _truncate(err or "", max_out),
                    "cancelled",
                )
            remaining = end - time.monotonic()
            if remaining <= 0:
                if proc.poll() is None:
                    proc.kill()
                out, err = proc.communicate(timeout=30)
                return (
                    _truncate(out or "", max_out),
                    _truncate(err or "", max_out),
                    "timeout",
                )
            try:
                out, err = proc.communicate(timeout=min(0.2, max(0.001, remaining)))
                return (
                    _truncate(out or "", max_out),
                    _truncate(err or "", max_out),
                    "ok",
                )
            except subprocess.TimeoutExpired:
                continue

    def _execute_subprocess(
        self,
        contract: ExecutionTaskContract,
        tool_call: ToolCallRequest,
        rollback_plan: RollbackPlan | None,
        *,
        dry_run: bool,
        cancellation_event: threading.Event | None,
    ) -> ToolExecutionResult:
        started = now_utc()
        max_out = contract.max_output_bytes or 64_000
        command_raw = str(tool_call.arguments.get("command") or tool_call.arguments.get("cmd") or "")

        if cancellation_event is not None and cancellation_event.is_set():
            return _cancelled_execution_result(
                contract, tool_call, started=started, rollback_plan=rollback_plan
            )

        if dry_run:
            return ToolExecutionResult(
                contract_id=contract.contract_id,
                tool_call_id=tool_call.tool_call_id,
                status="dry_run_completed",
                stdout=f"dry-run: would execute `{command_raw}`",
                started_at=started,
                completed_at=now_utc(),
                rollback_plan_id=rollback_plan.rollback_plan_id if rollback_plan else None,
            )

        if not self.allow_subprocess_execution:
            return ToolExecutionResult(
                contract_id=contract.contract_id,
                tool_call_id=tool_call.tool_call_id,
                status="blocked",
                stderr="Subprocess execution is disabled by runtime policy.",
                started_at=started,
                completed_at=now_utc(),
                error_message="subprocess_disabled",
                rollback_plan_id=rollback_plan.rollback_plan_id if rollback_plan else None,
            )

        try:
            argv = shlex.split(command_raw)
        except ValueError as exc:
            return ToolExecutionResult(
                contract_id=contract.contract_id,
                tool_call_id=tool_call.tool_call_id,
                status="failed",
                stderr=f"Invalid command: {exc}",
                started_at=started,
                completed_at=now_utc(),
                error_message="invalid_command",
            )

        if not argv:
            return ToolExecutionResult(
                contract_id=contract.contract_id,
                tool_call_id=tool_call.tool_call_id,
                status="blocked",
                stderr="Empty command.",
                started_at=started,
                completed_at=now_utc(),
                error_message="empty_command",
            )

        if not self._allowlisted(argv):
            return ToolExecutionResult(
                contract_id=contract.contract_id,
                tool_call_id=tool_call.tool_call_id,
                status="blocked",
                stderr="Command is not allowlisted by runtime policy.",
                started_at=started,
                completed_at=now_utc(),
                error_message="command_not_allowlisted",
            )

        timeout_s = max(0.001, (contract.max_runtime_ms or 60_000) / 1000.0)
        proc = subprocess.Popen(
            argv,
            cwd=self.workspace_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        kind = self._communicate_subprocess(
            proc,
            deadline_s=timeout_s,
            cancellation_event=cancellation_event,
            max_out=max_out,
        )
        stdout, stderr, outcome = kind
        code = proc.returncode

        if outcome == "cancelled":
            return ToolExecutionResult(
                contract_id=contract.contract_id,
                tool_call_id=tool_call.tool_call_id,
                status="failed",
                stdout=stdout,
                stderr=stderr or "Execution cancelled; subprocess terminated.",
                started_at=started,
                completed_at=now_utc(),
                error_message="cancelled",
                exit_code=code,
            )
        if outcome == "timeout":
            return ToolExecutionResult(
                contract_id=contract.contract_id,
                tool_call_id=tool_call.tool_call_id,
                status="timed_out",
                stdout=stdout,
                stderr=stderr or "Process timed out and was terminated.",
                started_at=started,
                completed_at=now_utc(),
                error_message="process_timeout_killed",
            )
        if code == 0:
            return ToolExecutionResult(
                contract_id=contract.contract_id,
                tool_call_id=tool_call.tool_call_id,
                status="completed",
                exit_code=code,
                stdout=stdout,
                stderr=stderr,
                started_at=started,
                completed_at=now_utc(),
            )
        return ToolExecutionResult(
            contract_id=contract.contract_id,
            tool_call_id=tool_call.tool_call_id,
            status="failed",
            exit_code=code,
            stdout=stdout,
            stderr=stderr,
            started_at=started,
            completed_at=now_utc(),
        )

    def _allowlisted(self, argv: list[str]) -> bool:
        cmd = argv[0]
        patterns = self.subprocess_allowlist.get(cmd)
        if patterns is None:
            return False
        joined = " ".join(argv[1:])
        dangerous = re.compile(r"(rm\s+-rf\s+/|curl[^|]*\|\s*sh|wget[^|]*\|\s*sh|git\s+push\s+--force)", re.I)
        if dangerous.search(f"{cmd} {joined}"):
            return False
        if not patterns:
            return True
        return any(re.search(p, joined) for p in patterns)
