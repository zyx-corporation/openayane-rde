"""Read-only summarization for audit logs and relation stores (Phase 5 P5-6)."""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from openayane_rde.core.models import AuditEvent
from openayane_rde.relation.context_loader import relation_record_to_context
from openayane_rde.relation.store import JSONRelationStore


def summarize_audit_jsonl(log_path: Path) -> dict[str, Any]:
    """Parse JSONL tolerantly: count valid :class:`AuditEvent` rows and collect defects."""

    malformed: list[dict[str, object]] = []
    action_counts: Counter[str] = Counter()
    id_counts: Counter[str] = Counter()
    lines_scanned = 0
    nonempty_lines = 0
    valid_events = 0

    with log_path.open(encoding="utf-8") as f:
        for line in f:
            lines_scanned += 1
            s = line.strip()
            if not s:
                continue
            nonempty_lines += 1
            try:
                data = json.loads(s)
                ev = AuditEvent.model_validate(data)
            except (json.JSONDecodeError, ValidationError, TypeError) as exc:
                malformed.append({"line": lines_scanned, "error": str(exc)})
                continue
            valid_events += 1
            id_counts[ev.event_id] += 1
            action_counts[str(ev.action)] += 1

    duplicate_event_ids = sorted(k for k, v in id_counts.items() if v > 1)

    return {
        "log_path": str(log_path.resolve()),
        "lines_scanned": lines_scanned,
        "nonempty_lines": nonempty_lines,
        "valid_events": valid_events,
        "malformed_lines": len(malformed),
        "malformed": malformed[:50],
        "truncated_malformed_reports": max(0, len(malformed) - 50),
        "actions": dict(action_counts),
        "duplicate_event_ids": duplicate_event_ids,
    }


def summarize_relation_json(store_path: Path) -> dict[str, Any]:
    store = JSONRelationStore(store_path)
    records = store.load_all()
    rows: list[dict[str, Any]] = []
    for key, rec in sorted(records.items(), key=lambda kv: kv[0]):
        ctx = relation_record_to_context(rec)
        rows.append(
            {
                "store_key": key,
                "relation_id": rec.relation_id,
                "subject_id": rec.subject_id,
                "object_id": rec.object_id,
                "relation_type": rec.relation_type,
                "trust": rec.trust,
                "stability": rec.stability,
                "context_affinity": rec.context_affinity,
                "interaction_count": rec.interaction_count,
                "drift_patterns": list(ctx.drift_patterns),
                "drift_pattern_counts": dict(ctx.drift_pattern_counts),
                "review_threshold_adjustment": rec.review_threshold_adjustment,
                "last_audit_event_id": rec.last_audit_event_id,
            }
        )
    return {
        "backend": "json",
        "path": str(store_path.resolve()),
        "record_count": len(rows),
        "records": rows,
    }


def summarize_relation_sqlite_readonly(store_path: Path) -> dict[str, Any]:
    """List relation rows using SQLite URI ``mode=ro`` (no schema migrations)."""

    uri = f"file:{store_path.resolve()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        conn.row_factory = sqlite3.Row
        rel_rows = conn.execute(
            "SELECT * FROM relation_records ORDER BY subject_id, object_id"
        ).fetchall()
        rows: list[dict[str, Any]] = []
        for row in rel_rows:
            rid = row["relation_id"]
            patterns = conn.execute(
                "SELECT kind, count FROM drift_patterns WHERE relation_id = ? ORDER BY kind",
                (rid,),
            ).fetchall()
            drift_counts = {str(p["kind"]): int(p["count"]) for p in patterns}
            rows.append(
                {
                    "relation_id": rid,
                    "subject_id": row["subject_id"],
                    "object_id": row["object_id"],
                    "relation_type": row["relation_type"],
                    "trust": float(row["trust"]),
                    "stability": float(row["stability"]),
                    "context_affinity": float(row["context_affinity"]),
                    "interaction_count": int(row["interaction_count"]),
                    "drift_pattern_counts": drift_counts,
                    "drift_patterns": [str(p["kind"]) for p in patterns],
                    "review_threshold_adjustment": float(row["review_threshold_adjustment"]),
                    "last_audit_event_id": row["last_audit_event_id"],
                }
            )
    finally:
        conn.close()

    return {
        "backend": "sqlite",
        "path": str(store_path.resolve()),
        "record_count": len(rows),
        "records": rows,
    }


def summarize_relation_store(backend: str, store_path: Path) -> dict[str, Any]:
    if backend == "json":
        return summarize_relation_json(store_path)
    if backend == "sqlite":
        return summarize_relation_sqlite_readonly(store_path)
    msg = f"Unknown relation backend: {backend!r}"
    raise ValueError(msg)
