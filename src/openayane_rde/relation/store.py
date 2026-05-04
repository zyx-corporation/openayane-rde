"""Persistent RelationStore (Phase 2 minimal JSON backend)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, runtime_checkable

from openayane_rde.core.models import RelationContext, RelationStoreRecord


@runtime_checkable
class RelationStore(Protocol):
    """Minimal relation persistence API (Phase 2)."""

    def get(self, subject_id: str, object_id: str) -> RelationStoreRecord | None:
        ...

    def upsert(self, record: RelationStoreRecord) -> None:
        ...

    def load_context(self, subject_id: str, object_id: str) -> RelationContext:
        ...


def _store_key(subject_id: str, object_id: str) -> str:
    return f"{subject_id}\x1f{object_id}"


class JSONRelationStore:
    """JSON file backing store for :class:`RelationStoreRecord` maps."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load_all(self) -> dict[str, RelationStoreRecord]:
        if not self.path.exists():
            return {}
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return {
            k: RelationStoreRecord.model_validate(v) for k, v in raw.items()
        }

    def save_all(self, records: dict[str, RelationStoreRecord]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {k: r.model_dump(mode="json") for k, r in records.items()}
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(self.path)

    def get(self, subject_id: str, object_id: str) -> RelationStoreRecord | None:
        return self.load_all().get(_store_key(subject_id, object_id))

    def upsert(self, record: RelationStoreRecord) -> None:
        all_r = self.load_all()
        all_r[_store_key(record.subject_id, record.object_id)] = record
        self.save_all(all_r)

    def load_context(self, subject_id: str, object_id: str) -> RelationContext:
        from openayane_rde.relation.context_loader import relation_record_to_context

        rec = self.get(subject_id, object_id)
        if rec is None:
            from openayane_rde.relation.context_loader import load_neutral_context

            return load_neutral_context(subject_id, object_id)
        return relation_record_to_context(rec)
