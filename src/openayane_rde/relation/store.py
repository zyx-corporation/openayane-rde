"""In-memory RelationStore for Phase 1.

Phase 2 will introduce persistent storage.
"""

from __future__ import annotations

from openayane_rde.core.models import RelationContext


class RelationStore:
    """In-memory key-value store for RelationContext objects.

    Phase 1 stub: no persistence.
    """

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], RelationContext] = {}

    def get(self, subject_id: str, object_id: str) -> RelationContext | None:
        return self._store.get((subject_id, object_id))

    def set(self, context: RelationContext) -> None:
        self._store[(context.subject_id, context.object_id)] = context

    def all(self) -> list[RelationContext]:
        return list(self._store.values())
