"""Rollback manager — file snapshots and validation (Phase 3).

Recovery playbook (operator-facing)
-----------------------------------
1. Confirm :class:`~openayane_rde.core.models.ExecutionTaskContract` uses
   ``rollback_strategy="file_snapshot"`` for filesystem writes you may need to revert.
2. Before mutating files, call :meth:`RollbackManager.create_plan` to capture snapshots
   under ``<workspace>/.relation_store/rollback/snapshots/``.
3. After a failed or high-risk run (see :func:`should_offer_rollback_for_execution`),
   call :meth:`RollbackManager.execute_rollback` or :meth:`RollbackManager.execute_rollback_with_audit`
   with the same plan id chain used for the execution.
4. If the plan reports ``manual_required`` / ``not_possible``, follow ``manual_steps``
   in :class:`~openayane_rde.core.models.RollbackPlan` and do not assume automated restore.
5. Verify restored paths and append audit evidence when ``audit_log_path`` is used.

This runtime does **not** guarantee transactional reversibility across arbitrary tools.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from openayane_rde.core.ids import new_id
from openayane_rde.core.models import (
    ExecutionTaskContract,
    RollbackPlan,
    RollbackResult,
    RollbackStrategyKind,
    ToolExecutionResult,
)
from openayane_rde.core.time import now_utc


def should_offer_rollback_for_execution(
    execution_result: ToolExecutionResult,
    *,
    gate_risk_level: str | None = None,
) -> bool:
    """Return True when operators should be prompted to consider rollback."""

    if execution_result.status in ("failed", "timed_out"):
        return True
    if gate_risk_level in ("high", "critical"):
        return True
    return False


def _under_workspace(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


class RollbackManager:
    """Create and execute rollback plans for simple file operations."""

    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir).resolve()
        self.snapshots_dir = self.root_dir / ".relation_store" / "rollback" / "snapshots"
        self.patches_dir = self.root_dir / ".relation_store" / "rollback" / "patches"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.patches_dir.mkdir(parents=True, exist_ok=True)

    def create_plan(self, contract: ExecutionTaskContract) -> RollbackPlan:
        rid = new_id("rbp")
        strategy: RollbackStrategyKind = contract.rollback_strategy
        targets = [t for t in contract.target_resources if t]
        snap_refs: list[str] = []
        manual_steps: list[str] = []
        validated = False
        msg: str | None = None

        if strategy == "none":
            validated = False
            msg = "No automated rollback strategy."
        elif strategy == "file_snapshot":
            snap_root = self.snapshots_dir / rid
            snap_root.mkdir(parents=True, exist_ok=True)
            for rel in targets:
                src = (self.root_dir / rel.lstrip("/")).resolve()
                if not src.is_file() or not _under_workspace(src, self.root_dir):
                    continue
                dest_snap = snap_root / rel
                dest_snap.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest_snap)
                snap_refs.append(str(dest_snap))
            validated = len(snap_refs) == len([t for t in targets if (self.root_dir / t.lstrip("/")).is_file()])
            if not validated:
                msg = "Snapshot incomplete or missing source files."
        elif strategy == "manual":
            manual_steps.append("Restore files manually per operator procedure.")
            validated = False
            msg = "Manual rollback required."
        else:
            validated = False
            msg = f"Strategy {strategy} not implemented in Phase 3 minimal."

        return RollbackPlan(
            rollback_plan_id=rid,
            contract_id=contract.contract_id,
            strategy=strategy,
            target_resources=targets,
            snapshot_refs=snap_refs,
            manual_steps=manual_steps,
            validated=validated and len(snap_refs) > 0,
            validation_message=msg,
        )

    def validate_plan(self, plan: RollbackPlan) -> RollbackPlan:
        if plan.strategy == "file_snapshot":
            ok = len(plan.snapshot_refs) > 0 and all(Path(p).is_file() for p in plan.snapshot_refs)
            return plan.model_copy(
                update={
                    "validated": ok,
                    "validation_message": None if ok else "Missing or invalid snapshot files.",
                }
            )
        return plan

    def execute_rollback(self, plan: RollbackPlan) -> RollbackResult:
        completed_at = now_utc()
        if plan.strategy == "none":
            return RollbackResult(
                rollback_plan_id=plan.rollback_plan_id,
                status="not_possible",
                completed_at=completed_at,
                error_message="No rollback strategy.",
            )
        if plan.strategy != "file_snapshot":
            return RollbackResult(
                rollback_plan_id=plan.rollback_plan_id,
                status="manual_required",
                completed_at=completed_at,
                error_message=plan.validation_message,
            )
        restored: list[str] = []
        try:
            pairs = list(zip(plan.snapshot_refs, plan.target_resources))
            if not pairs:
                return RollbackResult(
                    rollback_plan_id=plan.rollback_plan_id,
                    status="failed",
                    error_message="No snapshot pairs.",
                    completed_at=completed_at,
                )
            for snap, tr in pairs:
                dest = (self.root_dir / tr.lstrip("/")).resolve()
                if not _under_workspace(dest, self.root_dir):
                    continue
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(Path(snap), dest)
                restored.append(tr)
            return RollbackResult(
                rollback_plan_id=plan.rollback_plan_id,
                status="completed",
                restored_resources=restored,
                completed_at=completed_at,
            )
        except OSError as exc:
            return RollbackResult(
                rollback_plan_id=plan.rollback_plan_id,
                status="failed",
                error_message=str(exc),
                completed_at=completed_at,
            )

    def execute_rollback_with_audit(
        self,
        plan: RollbackPlan,
        *,
        audit_log_path: str | Path | None = None,
        trigger_reason: str = "",
    ) -> RollbackResult:
        """Run :meth:`execute_rollback` and optionally append ``rollback_completed`` / ``rollback_failed`` audit rows."""

        result = self.execute_rollback(plan)
        if audit_log_path is not None:
            from openayane_rde.audit.log import append_audit_event, audit_event_rollback_executed

            append_audit_event(
                audit_log_path,
                audit_event_rollback_executed(plan, result, trigger_reason=trigger_reason),
            )
        return result
