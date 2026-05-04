"""RelationStore update rules based on RDEResult.

Phase 1 stub: no-op. Phase 2 will implement actual update formulas.
"""

from __future__ import annotations

from openayane_rde.core.models import (
    AuditEvent,
    RDEResult,
    RelationContext,
    RelationUpdateSummary,
)
from openayane_rde.runtime.result import Phase1EvaluationResult


def update_relation_context(
    context: RelationContext,
    rde_result: RDEResult,
    audit_event: AuditEvent,
) -> RelationContext:
    """Return an updated RelationContext based on RDE classification.

    Phase 1: returns the original context unchanged (stub).
    Phase 2 will implement trust/stability/context_affinity update formulas.
    """
    return context


def update_relation_from_evaluation_result(
    result: Phase1EvaluationResult,
) -> RelationUpdateSummary:
    """Derive relation-store intent from a full Phase 1 evaluation bundle.

    Phase 2 will use ``task_contract``, ``generator_output``, ``rde_result``,
    and optional ``audit_event`` without re-running the pipeline. Phase 1 keeps
    ``update_relation_context`` as an identity stub but wires the call graph.
    """
    base = result.relation_context or RelationContext()
    if result.audit_event is None:
        return RelationUpdateSummary(
            context=base,
            updated=False,
            message="No audit event; relation context not correlated via audit pipeline.",
        )
    new_ctx = update_relation_context(base, result.rde_result, result.audit_event)
    return RelationUpdateSummary(
        context=new_ctx,
        updated=False,
        message="Phase 1 stub: update_relation_context is identity.",
    )
