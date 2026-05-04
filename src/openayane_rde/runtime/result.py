"""Phase 1 evaluation result: bundles diff, RDE, policy, and optional audit event."""

from __future__ import annotations

from pydantic import BaseModel

from openayane_rde.core.models import (
    AuditEvent,
    PolicyDecision,
    RDEResult,
    SemanticDelta,
    StructuralDiff,
)


class Phase1EvaluationResult(BaseModel):
    """Complete output of `run_phase1_evaluation()`.

    Exposes all intermediate artifacts for UI, CLI, audit review, and future
    RelationStore updates. `audit_event` is set only when `audit_log_path` was
    provided to the run function.
    """

    structural_diff: StructuralDiff
    semantic_delta: SemanticDelta
    rde_result: RDEResult
    policy_decision: PolicyDecision
    audit_event: AuditEvent | None = None

    model_config = {"extra": "forbid"}
