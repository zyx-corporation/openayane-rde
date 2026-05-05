"""RelationStore contract (JSON + SQLite backends)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from openayane_rde.core.models import DriftPattern, RelationStoreRecord
from openayane_rde.relation.sqlite_store import SQLiteRelationStore
from openayane_rde.relation.store import JSONRelationStore, relation_store_key


def test_relation_store_key_format() -> None:
    k = relation_store_key("sub ject", "obj\x1f")
    assert k.count("\x1f") >= 2
    assert k == relation_store_key("sub ject", "obj\x1f", "generator-document")


def _sqlite_store(path: Path) -> SQLiteRelationStore:
    s = SQLiteRelationStore(path)
    s.initialize()
    return s


@pytest.mark.parametrize(
    "factory",
    [
        pytest.param(lambda p: JSONRelationStore(p / "store.json"), id="json"),
        pytest.param(lambda p: _sqlite_store(p / "store.sqlite3"), id="sqlite"),
    ],
)
def test_relation_store_roundtrip(
    tmp_path: Path,
    factory: Callable[[Path], JSONRelationStore | SQLiteRelationStore],
) -> None:
    store_path = tmp_path / "root"
    store_path.mkdir()
    store = factory(store_path)
    rec = RelationStoreRecord(subject_id="s", object_id="o")
    store.upsert(rec)
    loaded = factory(store_path).get("s", "o")
    assert loaded is not None
    assert loaded.subject_id == "s"
    assert loaded.object_id == "o"
    assert loaded.relation_id == rec.relation_id


@pytest.mark.parametrize(
    "factory",
    [
        pytest.param(lambda p: JSONRelationStore(p / "store.json"), id="json"),
        pytest.param(lambda p: _sqlite_store(p / "store.sqlite3"), id="sqlite"),
    ],
)
def test_relation_store_neutral_load_context(
    tmp_path: Path,
    factory: Callable[[Path], JSONRelationStore | SQLiteRelationStore],
) -> None:
    store_path = tmp_path / "root"
    store_path.mkdir()
    store = factory(store_path)
    ctx = store.load_context("unknown-sub", "unknown-obj")
    assert ctx.subject_id == "unknown-sub"
    assert ctx.object_id == "unknown-obj"


@pytest.mark.parametrize(
    "factory",
    [
        pytest.param(lambda p: JSONRelationStore(p / "store.json"), id="json"),
        pytest.param(lambda p: _sqlite_store(p / "store.sqlite3"), id="sqlite"),
    ],
)
def test_relation_store_drift_patterns_roundtrip(
    tmp_path: Path,
    factory: Callable[[Path], JSONRelationStore | SQLiteRelationStore],
) -> None:
    store_path = tmp_path / "root"
    store_path.mkdir()
    store = factory(store_path)
    rec = RelationStoreRecord(
        subject_id="s",
        object_id="o",
        drift_patterns=[DriftPattern(kind="number_change", count=3, severity="high")],
    )
    store.upsert(rec)
    loaded = factory(store_path).get("s", "o")
    assert loaded is not None
    assert len(loaded.drift_patterns) == 1
    assert loaded.drift_patterns[0].kind == "number_change"
    assert loaded.drift_patterns[0].count == 3
