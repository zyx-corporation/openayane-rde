"""OpenAyane RDE: structural and semantic deviation evaluation for generative systems.

Phase 1 provides structural diff, RDE, policy, audit, and Phase1EvaluationResult.

Phase 2 adds JSON RelationStore, relation updates from audited evaluations,
allowed_delta keyword matching, enriched SemanticDelta extraction, and policy
adjustments from RelationContext history signals.
"""

from __future__ import annotations

from openayane_rde.core.models import (
    AuditEvent,
    GeneratorOutput,
    PolicyDecision,
    RDEResult,
    RelationContext,
    RelationStoreRecord,
    RelationUpdateSummary,
    SemanticDelta,
    StructuralDiff,
    TaskContract,
)
from openayane_rde.relation.store import JSONRelationStore
from openayane_rde.relation.update import update_relation_from_evaluation_result
from openayane_rde.runtime._flow import (
    run_phase1_evaluation,
    run_phase1_evaluation_from_post_execution_diff,
)
from openayane_rde.runtime.result import Phase1EvaluationResult

__all__ = [
    "TaskContract",
    "GeneratorOutput",
    "StructuralDiff",
    "SemanticDelta",
    "RDEResult",
    "PolicyDecision",
    "AuditEvent",
    "RelationContext",
    "RelationStoreRecord",
    "RelationUpdateSummary",
    "JSONRelationStore",
    "Phase1EvaluationResult",
    "run_phase1_evaluation",
    "run_phase1_evaluation_from_post_execution_diff",
    "update_relation_from_evaluation_result",
]
