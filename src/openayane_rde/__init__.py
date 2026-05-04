"""OpenAyane RDE: structural and semantic deviation evaluation for generative systems.

Phase 1 provides:
  - TaskContract / GeneratorOutput / StructuralDiff / RDEResult / PolicyDecision / AuditEvent models
  - MarkdownDiff, JsonDiff, PythonAstDiff structural diff engines
  - Minimal RDE classifier and Policy Bridge
  - Append-only AuditLog (JSONL)
  - Phase 1 runtime flow: run_phase1_evaluation() -> Phase1EvaluationResult
"""

from __future__ import annotations

from openayane_rde.core.models import (
    AuditEvent,
    GeneratorOutput,
    PolicyDecision,
    RDEResult,
    RelationContext,
    SemanticDelta,
    StructuralDiff,
    TaskContract,
)
from openayane_rde.runtime._flow import run_phase1_evaluation
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
    "Phase1EvaluationResult",
    "run_phase1_evaluation",
]
