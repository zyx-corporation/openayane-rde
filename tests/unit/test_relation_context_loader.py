"""RelationContext loading from store."""

from __future__ import annotations

from pathlib import Path

from openayane_rde.core.models import RelationStoreRecord
from openayane_rde.relation.context_loader import load_relation_context
from openayane_rde.relation.store import JSONRelationStore


def test_load_relation_context_unknown_returns_neutral(tmp_path: Path) -> None:
    store = JSONRelationStore(tmp_path / "x.json")
    ctx = load_relation_context("a", "b", store)
    assert ctx.subject_id == "a"
    assert ctx.object_id == "b"
    assert ctx.trust == 0.5


def test_load_relation_context_from_record(tmp_path: Path) -> None:
    store = JSONRelationStore(tmp_path / "x.json")
    store.upsert(
        RelationStoreRecord(subject_id="u", object_id="d", trust=0.3, stability=0.8)
    )
    ctx = load_relation_context("u", "d", store)
    assert ctx.trust == 0.3
    assert ctx.stability == 0.8
