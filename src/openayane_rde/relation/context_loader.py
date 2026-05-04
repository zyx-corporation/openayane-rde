"""RelationContext loader for OpenAyane RDE."""

from __future__ import annotations

from typing import TYPE_CHECKING

from openayane_rde.core.models import RelationContext, RelationStoreRecord

if TYPE_CHECKING:
    from openayane_rde.relation.store import RelationStore


def load_neutral_context(
    subject_id: str = "unknown",
    object_id: str = "unknown",
) -> RelationContext:
    """Return a neutral RelationContext when no history exists."""

    return RelationContext(
        subject_id=subject_id,
        object_id=object_id,
        trust=0.5,
        stability=0.5,
        context_affinity=0.5,
        interaction_count=0,
        last_delta_m=0.0,
        drift_patterns=[],
        drift_pattern_counts={},
        review_threshold_adjustment=0.0,
        generator_reliability_score=None,
        document_fragility_score=None,
    )


def relation_record_to_context(record: RelationStoreRecord) -> RelationContext:
    """Project a persisted record into runtime :class:`RelationContext`."""

    gen_rel = (
        record.generator_reliability_profile.reliability_score
        if record.generator_reliability_profile
        else None
    )
    doc_frag = (
        record.document_fragility_profile.fragility_score
        if record.document_fragility_profile
        else None
    )
    drift_labels: list[str] = [str(p.kind) for p in record.drift_patterns]
    drift_counts: dict[str, int] = {}
    for p in record.drift_patterns:
        k = str(p.kind)
        drift_counts[k] = drift_counts.get(k, 0) + p.count
    return RelationContext(
        subject_id=record.subject_id,
        object_id=record.object_id,
        trust=record.trust,
        stability=record.stability,
        context_affinity=record.context_affinity,
        interaction_count=record.interaction_count,
        last_delta_m=record.last_delta_m,
        drift_patterns=drift_labels,
        drift_pattern_counts=drift_counts,
        review_threshold_adjustment=record.review_threshold_adjustment,
        generator_reliability_score=gen_rel,
        document_fragility_score=doc_frag,
        last_updated_at=record.updated_at,
    )


def load_relation_context(
    subject_id: str,
    object_id: str,
    store: RelationStore,
) -> RelationContext:
    """Load relation-facing context from a Phase 2 relation store."""

    return store.load_context(subject_id, object_id)
