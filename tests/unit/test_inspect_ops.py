"""Tests for Phase 5 operational inspect helpers."""

from __future__ import annotations

from pathlib import Path

from openayane_rde.audit.log import append_event
from openayane_rde.cli.inspect_ops import summarize_audit_jsonl, summarize_relation_store
from openayane_rde.core.models import RelationStoreRecord
from openayane_rde.relation.store import JSONRelationStore
from openayane_rde.relation.sqlite_store import SQLiteRelationStore

from tests.unit.test_audit_log import make_event


def test_summarize_audit_valid_and_malformed(tmp_path: Path) -> None:
    log = tmp_path / "a.jsonl"
    ev = make_event()
    append_event(log, ev)
    with log.open("a", encoding="utf-8") as f:
        f.write("not json\n")

    summary = summarize_audit_jsonl(log)
    assert summary["valid_events"] == 1
    assert summary["malformed_lines"] == 1
    assert summary["actions"].get("evaluate_rde") == 1
    assert summary["malformed"][0]["line"] == 2


def test_summarize_audit_duplicate_event_ids(tmp_path: Path) -> None:
    log = tmp_path / "d.jsonl"
    line = make_event(event_id="dup").model_dump_json() + "\n"
    log.write_text(line + line, encoding="utf-8")
    summary = summarize_audit_jsonl(log)
    assert summary["valid_events"] == 2
    assert "dup" in summary["duplicate_event_ids"]


def test_summarize_relation_json_empty(tmp_path: Path) -> None:
    p = tmp_path / "rel.json"
    summary = summarize_relation_store("json", p)
    assert summary["record_count"] == 0


def test_summarize_relation_json_with_record(tmp_path: Path) -> None:
    p = tmp_path / "rel.json"
    store = JSONRelationStore(p)
    rec = RelationStoreRecord(subject_id="g1", object_id="doc1", trust=0.7)
    store.upsert(rec)
    summary = summarize_relation_store("json", p)
    assert summary["record_count"] == 1
    assert summary["records"][0]["subject_id"] == "g1"
    assert summary["records"][0]["trust"] == 0.7


def test_summarize_relation_sqlite_readonly(tmp_path: Path) -> None:
    db = tmp_path / "r.sqlite3"
    sql_store = SQLiteRelationStore(db)
    sql_store.initialize()
    rec = RelationStoreRecord(subject_id="sg", object_id="od", stability=0.61)
    sql_store.upsert(rec)
    summary = summarize_relation_store("sqlite", db)
    assert summary["backend"] == "sqlite"
    assert summary["record_count"] == 1
    assert summary["records"][0]["stability"] == 0.61
