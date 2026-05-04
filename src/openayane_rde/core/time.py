"""UTC timestamp helpers for OpenAyane RDE."""

from __future__ import annotations

from datetime import datetime, timezone


def now_utc() -> datetime:
    """Return the current time in UTC."""
    return datetime.now(tz=timezone.utc)


def now_utc_iso() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return now_utc().isoformat()
