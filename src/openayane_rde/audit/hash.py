"""SHA-256 hash utilities for OpenAyane RDE audit."""

from __future__ import annotations

import hashlib


def sha256_text(text: str) -> str:
    """Compute SHA-256 hash of UTF-8 encoded text.

    Returns a string in the format 'sha256:<64 hex chars>'.
    """
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
