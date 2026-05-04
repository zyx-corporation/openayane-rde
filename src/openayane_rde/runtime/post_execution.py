"""Post-execution diff bundle for Phase 3 follow-up RDE."""

from __future__ import annotations

from openayane_rde.core.models import PostExecutionDiff, ToolExecutionResult
from openayane_rde.runtime._flow import run_phase1_evaluation_from_post_execution_diff

__all__ = ["build_post_execution_diff", "run_phase1_evaluation_from_post_execution_diff"]


def build_post_execution_diff(
    contract_id: str,
    result: ToolExecutionResult,
) -> PostExecutionDiff:
    """Construct a minimal PostExecutionDiff from runtime output."""

    return PostExecutionDiff(
        contract_id=contract_id,
        changed_resources=list(result.changed_resources),
        unexpected_side_effects=[],
        protected_resource_changes=[],
    )
