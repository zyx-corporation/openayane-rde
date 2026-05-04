"""RelationContext loader for OpenAyane RDE.

Phase 1: returns a neutral stub RelationContext.
"""

from __future__ import annotations

from openayane_rde.core.models import RelationContext


def load_neutral_context(
    subject_id: str = "unknown",
    object_id: str = "unknown",
) -> RelationContext:
    """Return a neutral RelationContext stub for Phase 1.

    All scores default to 0.5 (neutral) with no drift patterns recorded.
    """
    return RelationContext(
        subject_id=subject_id,
        object_id=object_id,
        trust=0.5,
        stability=0.5,
        context_affinity=0.5,
        interaction_count=0,
        last_delta_m=0.0,
        drift_patterns=[],
    )
