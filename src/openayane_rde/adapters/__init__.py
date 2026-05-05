"""Phase 5 adapters: external context → TaskContract / evidence (no evaluation bypass)."""

from openayane_rde.adapters.filesystem import FilesystemAdapter
from openayane_rde.adapters.types import (
    AdapterContext,
    AdapterSideEffectProfile,
    FilesystemAdapterSource,
    OpenAyaneAdapter,
)

__all__ = [
    "AdapterContext",
    "AdapterSideEffectProfile",
    "FilesystemAdapter",
    "FilesystemAdapterSource",
    "OpenAyaneAdapter",
]
