"""SQLite relation store (Phase 3)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from openayane_rde.core.models import (
    DriftPattern,
    RelationStoreRecord,
    ReviewDecision,
    ReviewRequest,
    ToolCallRisk,
)
from openayane_rde.relation.context_loader import relation_record_to_context
from openayane_rde.relation.sqlite_store import SCHEMA_VERSION, SQLiteRelationStore
from openayane_rde.relation.store import JSONRelationStore


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


def test_import_from_json_file_roundtrip(tmp_path: Path) -> None:
    jpath = tmp_path / "rel.json"
    jstore = JSONRelationStore(jpath)
    r1 = RelationStoreRecord(subject_id="s1", object_id="o1", trust=0.31)
    r2 = RelationStoreRecord(
        subject_id="s2",
        object_id="o2",
        trust=0.72,
        drift_patterns=[DriftPattern(kind="number_change", count=1)],
    )
    jstore.upsert(r1)
    jstore.upsert(r2)
    spath = tmp_path / "migrated.sqlite3"
    sql = SQLiteRelationStore(spath)
    assert sql.import_from_json_file(jpath) == 2
    g1 = sql.get("s1", "o1")
    g2 = sql.get("s2", "o2")
    assert g1 is not None and g1.trust == 0.31
    assert g2 is not None
    assert g2.trust == 0.72
    assert len(g2.drift_patterns) == 1
    assert g2.drift_patterns[0].kind == "number_change"


def test_import_from_json_file_empty(tmp_path: Path) -> None:
    jpath = tmp_path / "empty.json"
    jpath.write_text("{}", encoding="utf-8")
    sql = SQLiteRelationStore(tmp_path / "e.sqlite3")
    assert sql.import_from_json_file(jpath) == 0


def test_import_from_json_rolls_back_on_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    jpath = tmp_path / "rel.json"
    jstore = JSONRelationStore(jpath)
    jstore.upsert(RelationStoreRecord(subject_id="a", object_id="b"))
    jstore.upsert(RelationStoreRecord(subject_id="c", object_id="d"))
    spath = tmp_path / "t.sqlite3"
    store = SQLiteRelationStore(spath)
    n_calls = 0
    real_upsert = store._upsert_record

    def fail_second(conn: sqlite3.Connection, rec: RelationStoreRecord) -> None:
        nonlocal n_calls
        n_calls += 1
        if n_calls == 2:
            raise RuntimeError("simulated failure")
        real_upsert(conn, rec)

    monkeypatch.setattr(store, "_upsert_record", fail_second)
    with pytest.raises(RuntimeError, match="simulated"):
        store.import_from_json_file(jpath)
    after = SQLiteRelationStore(spath)
    after.initialize()
    assert after.get("a", "b") is None
    assert after.get("c", "d") is None
