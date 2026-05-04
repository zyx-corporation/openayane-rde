"""JSONRelationStore persistence."""

from __future__ import annotations

from pathlib import Path

from openayane_rde.core.models import RelationStoreRecord
from openayane_rde.relation.store import JSONRelationStore


def test_json_relation_store_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "store.json"
    store = JSONRelationStore(path)
    rec = RelationStoreRecord(subject_id="s", object_id="o")
    store.upsert(rec)
    loaded = JSONRelationStore(path).get("s", "o")
    assert loaded is not None
    assert loaded.subject_id == "s"
    assert loaded.object_id == "o"
    assert loaded.relation_id == rec.relation_id
