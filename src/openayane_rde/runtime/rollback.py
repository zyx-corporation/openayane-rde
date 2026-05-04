"""Rollback manager — file snapshots and validation (Phase 3)."""

from __future__ import annotations

import shutil
from pathlib import Path

from openayane_rde.core.ids import new_id
from openayane_rde.core.models import (
    ExecutionTaskContract,
    RollbackPlan,
    RollbackResult,
    RollbackStrategyKind,
)
from openayane_rde.core.time import now_utc


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
