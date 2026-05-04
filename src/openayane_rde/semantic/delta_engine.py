"""SemanticDelta Engine interface (Phase 1: delegates to stub)."""

from __future__ import annotations

from openayane_rde.core.models import SemanticDelta, StructuralDiff, TaskContract
from openayane_rde.semantic.stub import semantic_delta_stub


def estimate_semantic_delta(
    structural_diff: StructuralDiff,
    contract: TaskContract,
) -> SemanticDelta:
    """Estimate semantic delta from structural diff.

    Phase 1: stub implementation only.
    """
    return semantic_delta_stub(structural_diff, contract)
