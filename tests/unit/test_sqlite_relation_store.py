"""SQLite relation store (Phase 3)."""

from __future__ import annotations

from pathlib import Path

from openayane_rde.core.models import (
    DriftPattern,
    RelationStoreRecord,
    ReviewDecision,
    ReviewRequest,
    ToolCallRisk,
)
from openayane_rde.relation.context_loader import relation_record_to_context
from openayane_rde.relation.sqlite_store import SCHEMA_VERSION, SQLiteRelationStore


def test_sqlite_applied_schema_versions(tmp_path: Path) -> None:
    store = SQLiteRelationStore(tmp_path / "schema_ver.sqlite3")
    assert store.applied_schema_versions() == [SCHEMA_VERSION]
    assert store.applied_schema_versions() == [SCHEMA_VERSION]


def test_sqlite_initialize_upsert_load_context(tmp_path: Path) -> None:
    p = tmp_path / "r.sqlite3"
    store = SQLiteRelationStore(p)
    store.initialize()
    rec = RelationStoreRecord(
        subject_id="a",
        object_id="b",
        trust=0.4,
        drift_patterns=[DriftPattern(kind="number_change", count=2)],
    )
    store.upsert(rec)
    out = store.get("a", "b")
    assert out is not None
    assert out.trust == 0.4
    assert len(out.drift_patterns) == 1
    assert out.drift_patterns[0].count == 2
    ctx = store.load_context("a", "b")
    assert ctx.drift_pattern_counts.get("number_change") == 2
    assert relation_record_to_context(out).trust == 0.4


def test_sqlite_review_decision_persisted(tmp_path: Path) -> None:
    store = SQLiteRelationStore(tmp_path / "rev.sqlite3")
    store.initialize()
    rr = ReviewRequest(
        contract_id="c1",
        tool_call_id="t1",
        agent_id="ag",
        reason="test",
        risk=ToolCallRisk(risk_level="high", risk_score=0.8),
    )
    store.create_review_request(rr)
    decision = ReviewDecision(
        review_request_id=rr.review_request_id,
        reviewer_id="u1",
        decision="reject",
        reason="no",
    )
    store.append_review_decision(decision)
