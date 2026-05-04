"""RelationContext projection from RelationStoreRecord."""

from __future__ import annotations

from openayane_rde.core.models import DriftPattern, RelationStoreRecord
from openayane_rde.relation.context_loader import relation_record_to_context


def test_relation_record_to_context_drift_pattern_counts() -> None:
    record = RelationStoreRecord(
        subject_id="gen",
        object_id="doc",
        drift_patterns=[
            DriftPattern(kind="number_change", count=3),
            DriftPattern(kind="self_report_mismatch", count=1),
        ],
    )
    ctx = relation_record_to_context(record)
    assert ctx.drift_pattern_counts == {"number_change": 3, "self_report_mismatch": 1}
    assert ctx.drift_patterns == ["number_change", "self_report_mismatch"]


def test_relation_record_to_context_merges_counts_for_same_kind() -> None:
    record = RelationStoreRecord(
        subject_id="g",
        object_id="d",
        drift_patterns=[
            DriftPattern(kind="number_change", count=2),
            DriftPattern(kind="number_change", count=1),
        ],
    )
    ctx = relation_record_to_context(record)
    assert ctx.drift_pattern_counts == {"number_change": 3}
