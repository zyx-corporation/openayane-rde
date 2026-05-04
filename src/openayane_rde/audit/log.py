"""Append-only JSONL AuditLog writer and reader for OpenAyane RDE."""

from __future__ import annotations

import json
from pathlib import Path

from openayane_rde.core.errors import AuditError
from openayane_rde.core.models import AuditEvent


def append_event(path: str | Path, event: AuditEvent) -> None:
    """Append an AuditEvent to a JSONL file.

    Creates the file and parent directories if they do not exist.
    Each line in the JSONL file is one JSON-serialized AuditEvent.
    """
    log_path = Path(path)
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        line = event.model_dump_json() + "\n"
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line)
    except OSError as exc:
        raise AuditError(f"Failed to write audit event to {path}: {exc}") from exc


def load_events(path: str | Path) -> list[AuditEvent]:
    """Load all AuditEvents from a JSONL file.

    Returns an empty list if the file does not exist.
    Raises AuditError if the file contains invalid JSON lines.
    """
    log_path = Path(path)
    if not log_path.exists():
        return []
    events: list[AuditEvent] = []
    try:
        with log_path.open("r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    events.append(AuditEvent.model_validate(data))
                except (json.JSONDecodeError, Exception) as exc:
                    raise AuditError(
                        f"Failed to parse audit event at line {lineno} in {path}: {exc}"
                    ) from exc
    except OSError as exc:
        raise AuditError(f"Failed to read audit log {path}: {exc}") from exc
    return events
