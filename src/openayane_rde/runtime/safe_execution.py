"""Safe Execution Runtime — bounded file/subprocess execution (Phase 3)."""

from __future__ import annotations

import re
import shlex
import subprocess
import time
from pathlib import Path

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


def _truncate(s: str, max_bytes: int | None) -> str:
    if max_bytes is None or max_bytes <= 0:
        return s
    b = s.encode("utf-8")
    if len(b) <= max_bytes:
        return s
    return b[:max_bytes].decode("utf-8", errors="replace") + "\n[truncated]"


class SafeExecutionRuntime:
    """Application-level safe execution (not a full OS sandbox)."""

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
    ) -> ToolExecutionResult:
        """Execute or simulate a tool call within workspace and policy limits."""

        started = now_utc()
        max_ms = contract.max_runtime_ms
        max_out = contract.max_output_bytes or 64_000

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
            return self._execute_subprocess(contract, tool_call, rollback_plan, dry_run=dry_run)

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

        if max_ms is not None:
            time.sleep(min(max_ms / 1000.0, 0.001))

        if contract.action_type == "read":
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

    def _execute_subprocess(
        self,
        contract: ExecutionTaskContract,
        tool_call: ToolCallRequest,
        rollback_plan: RollbackPlan | None,
        *,
        dry_run: bool,
    ) -> ToolExecutionResult:
        started = now_utc()
        max_out = contract.max_output_bytes or 64_000
        command_raw = str(tool_call.arguments.get("command") or tool_call.arguments.get("cmd") or "")

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
        try:
            completed = subprocess.run(
                argv,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
            if completed.returncode == 0:
                return ToolExecutionResult(
                    contract_id=contract.contract_id,
                    tool_call_id=tool_call.tool_call_id,
                    status="completed",
                    exit_code=completed.returncode,
                    stdout=_truncate(completed.stdout or "", max_out),
                    stderr=_truncate(completed.stderr or "", max_out),
                    started_at=started,
                    completed_at=now_utc(),
                )
            return ToolExecutionResult(
                contract_id=contract.contract_id,
                tool_call_id=tool_call.tool_call_id,
                status="failed",
                exit_code=completed.returncode,
                stdout=_truncate(completed.stdout or "", max_out),
                stderr=_truncate(completed.stderr or "", max_out),
                started_at=started,
                completed_at=now_utc(),
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout if isinstance(exc.stdout, str) else ""
            stderr = exc.stderr if isinstance(exc.stderr, str) else ""
            return ToolExecutionResult(
                contract_id=contract.contract_id,
                tool_call_id=tool_call.tool_call_id,
                status="timed_out",
                stdout=_truncate(stdout, max_out),
                stderr=_truncate(stderr, max_out) or "Process timed out and was terminated.",
                started_at=started,
                completed_at=now_utc(),
                error_message="process_timeout_killed",
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
