"""Proof-of-personhood / external identity adapter surface (interface only).

Phase 4 does not implement cryptographic PoP-UID; callers supply concrete adapters.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class PopUidAdapter(Protocol):
    """Hook for verifying whether a subject may bind critical institutional actions."""

    def has_valid_pop(self, subject_id: str) -> bool:
        """Return True when the adapter considers PoP / institutional identity satisfied."""

        ...
