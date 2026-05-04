"""Rollback stub for Phase 1.

Phase 2+ will implement actual rollback logic.
"""

from __future__ import annotations

from openayane_rde.core.models import TaskContract


def rollback(contract: TaskContract) -> None:
    """Stub rollback. Phase 1: no-op."""
