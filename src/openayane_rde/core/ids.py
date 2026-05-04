"""Stable prefixed ID generation for OpenAyane RDE objects."""

from __future__ import annotations

import uuid


def new_id(prefix: str) -> str:
    """Generate a unique prefixed ID.

    Examples:
        new_id("tc")    -> "tc_<uuid>"
        new_id("go")    -> "go_<uuid>"
        new_id("sdiff") -> "sdiff_<uuid>"
        new_id("rde")   -> "rde_<uuid>"
        new_id("audit") -> "audit_<uuid>"
    """
    uid = uuid.uuid4().hex
    return f"{prefix}_{uid}"
