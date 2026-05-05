"""SQLite persistence for relation state, execution events, and review (Phase 3).

Migration from :class:`~openayane_rde.relation.store.JSONRelationStore`
------------------------------------------------------------------------
Export the JSON store (same on-disk file used by ``JSONRelationStore``), then call
``SQLiteRelationStore.import_from_json_file`` targeting a **new** SQLite path.
The import runs in a single transaction; on failure the database file ends with no partial
relation rows from that import (the transaction rolls back).

Rollback-safe operational notes
-------------------------------
* Keep the JSON snapshot until you have verified reads from SQLite (``get`` / ``load_context``).
* To replace an existing ``*.sqlite3``, copy it to ``*.sqlite3.bak`` first; restore from backup if
  post-migration checks fail.
* Application ``upsert`` calls use one transaction each so ``relation_records`` and
  ``drift_patterns`` stay consistent on error.

See ``tests/unit/test_relation_store.py`` (parametrized contract tests).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from openayane_rde.core.ids import new_id
from openayane_rde.core.models import (
    DocumentFragilityProfile,
    DriftPattern,
    ExecutionGateDecision,
    GeneratorReliabilityProfile,
    RelationContext,
    RelationStoreRecord,
    ReviewDecision,
    ReviewRequest,
    RollbackPlan,
    ToolExecutionResult,
)
from openayane_rde.core.time import now_utc


def _parse_iso_datetime(raw: str) -> datetime:
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    return datetime.fromisoformat(raw)

SCHEMA_VERSION = 1

_INIT_SQL = """
CREATE TABLE IF NOT EXISTS relation_records (
  relation_id TEXT PRIMARY KEY,
  subject_id TEXT NOT NULL,
  object_id TEXT NOT NULL,
  relation_type TEXT NOT NULL,
  trust REAL NOT NULL,
  stability REAL NOT NULL,
  context_affinity REAL NOT NULL,
  interaction_count INTEGER NOT NULL,
  critical_corruption_count INTEGER NOT NULL,
  suspicious_drift_count INTEGER NOT NULL,
  self_report_mismatch_count INTEGER NOT NULL,
  review_threshold_adjustment REAL NOT NULL,
  last_delta_m REAL NOT NULL,
  last_audit_event_id TEXT,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(subject_id, object_id, relation_type)
);

CREATE TABLE IF NOT EXISTS drift_patterns (
  pattern_id TEXT PRIMARY KEY,
  relation_id TEXT NOT NULL,
  kind TEXT NOT NULL,
  count INTEGER NOT NULL,
  severity TEXT NOT NULL,
  examples_json TEXT NOT NULL DEFAULT '[]',
  last_seen_at TEXT NOT NULL,
  FOREIGN KEY(relation_id) REFERENCES relation_records(relation_id)
);

CREATE TABLE IF NOT EXISTS execution_events (
  execution_event_id TEXT PRIMARY KEY,
  contract_id TEXT NOT NULL,
  tool_call_id TEXT NOT NULL,
  agent_id TEXT NOT NULL,
  tool_name TEXT NOT NULL,
  action_type TEXT NOT NULL,
  gate_action TEXT NOT NULL,
  risk_level TEXT NOT NULL,
  status TEXT NOT NULL,
  audit_event_id TEXT,
  rollback_plan_id TEXT,
  review_request_id TEXT,
  created_at TEXT NOT NULL,
  metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS review_requests (
  review_request_id TEXT PRIMARY KEY,
  contract_id TEXT NOT NULL,
  tool_call_id TEXT NOT NULL,
  agent_id TEXT NOT NULL,
  status TEXT NOT NULL,
  reason TEXT NOT NULL,
  risk_json TEXT NOT NULL,
  rollback_plan_json TEXT,
  rde_result_json TEXT,
  relation_context_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS review_decisions (
  review_decision_id TEXT PRIMARY KEY,
  review_request_id TEXT NOT NULL,
  reviewer_id TEXT NOT NULL,
  decision TEXT NOT NULL,
  reason TEXT NOT NULL,
  approved_at TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(review_request_id) REFERENCES review_requests(review_request_id)
);

CREATE TABLE IF NOT EXISTS rollback_plans (
  rollback_plan_id TEXT PRIMARY KEY,
  contract_id TEXT NOT NULL,
  strategy TEXT NOT NULL,
  target_resources_json TEXT NOT NULL,
  snapshot_refs_json TEXT NOT NULL DEFAULT '[]',
  reverse_patch_path TEXT,
  manual_steps_json TEXT NOT NULL DEFAULT '[]',
  validated INTEGER NOT NULL DEFAULT 0,
  validation_message TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS schema_migrations (
  version INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  applied_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_relation_subject_object
  ON relation_records(subject_id, object_id);

CREATE INDEX IF NOT EXISTS idx_drift_relation_kind
  ON drift_patterns(relation_id, kind);

CREATE INDEX IF NOT EXISTS idx_execution_contract
  ON execution_events(contract_id);

CREATE INDEX IF NOT EXISTS idx_execution_tool_call
  ON execution_events(tool_call_id);

CREATE INDEX IF NOT EXISTS idx_review_status
  ON review_requests(status);
"""


class SQLiteRelationStore:
    """Phase 3 SQLite backend (single-process writer assumption)."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self) -> None:
        with self._connect() as conn:
            conn.executescript(_INIT_SQL)
            row = conn.execute(
                "SELECT 1 FROM schema_migrations WHERE version = ?", (SCHEMA_VERSION,)
            ).fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)",
                    (SCHEMA_VERSION, "phase3_initial", now_utc().isoformat()),
                )

    def applied_schema_versions(self) -> list[int]:
        """Ordered list of applied schema migration versions (see ``schema_migrations``)."""

        self.initialize()
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT version FROM schema_migrations ORDER BY version ASC"
            ).fetchall()
        return [int(r[0]) for r in rows]

    def import_from_json_file(self, json_path: str | Path) -> int:
        """Load a JSON relation snapshot and upsert all rows in one transaction.

        Returns the number of records imported. Uses :class:`JSONRelationStore` parsing
        (including legacy key compatibility inside ``load_all``).
        """

        from openayane_rde.relation.store import JSONRelationStore

        src = JSONRelationStore(json_path)
        records = src.load_all()
        self.initialize()
        if not records:
            return 0
        with self._connect() as conn:
            conn.execute("BEGIN")
            try:
                for rec in records.values():
                    self._upsert_record(conn, rec)
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise
        return len(records)

    def _metadata_pack(self, record: RelationStoreRecord) -> dict[str, Any]:
        meta: dict[str, Any] = {}
        if record.self_report_mismatch_item_count:
            meta["self_report_mismatch_item_count"] = record.self_report_mismatch_item_count
        if record.generator_reliability_profile is not None:
            meta["generator_reliability_profile"] = (
                record.generator_reliability_profile.model_dump(mode="json")
            )
        if record.document_fragility_profile is not None:
            meta["document_fragility_profile"] = (
                record.document_fragility_profile.model_dump(mode="json")
            )
        return meta

    def _metadata_unpack(
        self,
        meta: dict[str, Any],
        subject_id: str,
        object_id: str,
    ) -> tuple[int, GeneratorReliabilityProfile | None, DocumentFragilityProfile | None]:
        sm_item = int(meta.get("self_report_mismatch_item_count", 0))
        gen: GeneratorReliabilityProfile | None = None
        doc: DocumentFragilityProfile | None = None
        if raw_g := meta.get("generator_reliability_profile"):
            gen = GeneratorReliabilityProfile.model_validate(raw_g)
        if raw_d := meta.get("document_fragility_profile"):
            doc = DocumentFragilityProfile.model_validate(raw_d)
        if gen is None:
            gen = GeneratorReliabilityProfile(generator_id=f"{subject_id}:default")
        if doc is None:
            doc = DocumentFragilityProfile(document_id=object_id)
        return sm_item, gen, doc

    def get(
        self,
        subject_id: str,
        object_id: str,
        relation_type: str = "generator-document",
    ) -> RelationStoreRecord | None:
        self.initialize()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM relation_records
                WHERE subject_id = ? AND object_id = ? AND relation_type = ?
                """,
                (subject_id, object_id, relation_type),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_record(conn, dict(row))

    def _row_to_record(self, conn: sqlite3.Connection, row: dict[str, Any]) -> RelationStoreRecord:
        meta = json.loads(row["metadata_json"] or "{}")
        sm_item, gen, doc = self._metadata_unpack(meta, row["subject_id"], row["object_id"])
        rid = row["relation_id"]
        patterns: list[DriftPattern] = []
        for pr in conn.execute(
            "SELECT * FROM drift_patterns WHERE relation_id = ?", (rid,)
        ).fetchall():
            p = dict(pr)
            examples = json.loads(p["examples_json"] or "[]")
            patterns.append(
                DriftPattern(
                    pattern_id=p["pattern_id"],
                    kind=p["kind"],
                    count=p["count"],
                    severity=p["severity"],
                    examples=examples,
                    last_seen_at=_parse_iso_datetime(p["last_seen_at"]),
                )
            )
        return RelationStoreRecord(
            relation_id=rid,
            subject_id=row["subject_id"],
            object_id=row["object_id"],
            relation_type=row["relation_type"],
            trust=row["trust"],
            stability=row["stability"],
            context_affinity=row["context_affinity"],
            interaction_count=row["interaction_count"],
            critical_corruption_count=row["critical_corruption_count"],
            suspicious_drift_count=row["suspicious_drift_count"],
            self_report_mismatch_count=row["self_report_mismatch_count"],
            self_report_mismatch_item_count=sm_item,
            drift_patterns=patterns,
            generator_reliability_profile=gen,
            document_fragility_profile=doc,
            review_threshold_adjustment=row["review_threshold_adjustment"],
            last_delta_m=row["last_delta_m"],
            last_audit_event_id=row["last_audit_event_id"],
            updated_at=_parse_iso_datetime(row["updated_at"]),
        )

    def _upsert_record(self, conn: sqlite3.Connection, record: RelationStoreRecord) -> None:
        meta = self._metadata_pack(record)
        meta_json = json.dumps(meta)
        updated_iso = record.updated_at.isoformat()
        cur = conn.execute(
            """
            SELECT relation_id, created_at FROM relation_records
            WHERE subject_id = ? AND object_id = ? AND relation_type = ?
            """,
            (record.subject_id, record.object_id, record.relation_type),
        ).fetchone()
        rel_id = record.relation_id if cur is None else str(cur["relation_id"])
        created_iso = updated_iso if cur is None else str(cur["created_at"])
        if cur is None:
            conn.execute(
                """
                INSERT INTO relation_records (
                  relation_id, subject_id, object_id, relation_type,
                  trust, stability, context_affinity, interaction_count,
                  critical_corruption_count, suspicious_drift_count,
                  self_report_mismatch_count, review_threshold_adjustment,
                  last_delta_m, last_audit_event_id, metadata_json,
                  created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rel_id,
                    record.subject_id,
                    record.object_id,
                    record.relation_type,
                    record.trust,
                    record.stability,
                    record.context_affinity,
                    record.interaction_count,
                    record.critical_corruption_count,
                    record.suspicious_drift_count,
                    record.self_report_mismatch_count,
                    record.review_threshold_adjustment,
                    record.last_delta_m,
                    record.last_audit_event_id,
                    meta_json,
                    created_iso,
                    updated_iso,
                ),
            )
        else:
            conn.execute(
                """
                UPDATE relation_records SET
                  trust = ?, stability = ?, context_affinity = ?, interaction_count = ?,
                  critical_corruption_count = ?, suspicious_drift_count = ?,
                  self_report_mismatch_count = ?, review_threshold_adjustment = ?,
                  last_delta_m = ?, last_audit_event_id = ?, metadata_json = ?,
                  updated_at = ?
                WHERE relation_id = ?
                """,
                (
                    record.trust,
                    record.stability,
                    record.context_affinity,
                    record.interaction_count,
                    record.critical_corruption_count,
                    record.suspicious_drift_count,
                    record.self_report_mismatch_count,
                    record.review_threshold_adjustment,
                    record.last_delta_m,
                    record.last_audit_event_id,
                    meta_json,
                    updated_iso,
                    rel_id,
                ),
            )
        conn.execute("DELETE FROM drift_patterns WHERE relation_id = ?", (rel_id,))
        for dp in record.drift_patterns:
            conn.execute(
                """
                INSERT INTO drift_patterns (
                  pattern_id, relation_id, kind, count, severity,
                  examples_json, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dp.pattern_id,
                    rel_id,
                    dp.kind,
                    dp.count,
                    dp.severity,
                    json.dumps(dp.examples),
                    dp.last_seen_at.isoformat(),
                ),
            )

    def upsert(self, record: RelationStoreRecord) -> None:
        self.initialize()
        with self._connect() as conn:
            conn.execute("BEGIN")
            try:
                self._upsert_record(conn, record)
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def load_context(
        self,
        subject_id: str,
        object_id: str,
        relation_type: str = "generator-document",
    ) -> RelationContext:
        from openayane_rde.relation.context_loader import (
            load_neutral_context,
            relation_record_to_context,
        )

        rec = self.get(subject_id, object_id, relation_type)
        if rec is None:
            return load_neutral_context(subject_id, object_id)
        return relation_record_to_context(rec)

    def append_execution_event(
        self,
        event: ExecutionGateDecision | ToolExecutionResult,
        *,
        agent_id: str = "",
        tool_name: str = "",
        tool_call_id: str = "",
        action_type: str = "unknown",
    ) -> None:
        self.initialize()
        eid = new_id("exeve")
        created = now_utc().isoformat()
        if isinstance(event, ExecutionGateDecision):
            meta = event.model_dump(mode="json")
            conn_d: dict[str, Any] = {
                "execution_event_id": eid,
                "contract_id": event.contract_id,
                "tool_call_id": tool_call_id or meta.get("contract_id", ""),
                "agent_id": agent_id or "unknown",
                "tool_name": tool_name or "unknown",
                "action_type": action_type,
                "gate_action": event.policy_action,
                "risk_level": event.risk.risk_level,
                "status": "decided",
                "audit_event_id": event.audit_event_id,
                "rollback_plan_id": None,
                "review_request_id": event.review_request_id,
                "created_at": created,
                "metadata_json": json.dumps(meta),
            }
        else:
            meta = event.model_dump(mode="json")
            conn_d = {
                "execution_event_id": eid,
                "contract_id": event.contract_id,
                "tool_call_id": event.tool_call_id,
                "agent_id": agent_id or "unknown",
                "tool_name": tool_name or "unknown",
                "action_type": action_type,
                "gate_action": "executed",
                "risk_level": "unknown",
                "status": event.status,
                "audit_event_id": event.audit_event_id,
                "rollback_plan_id": event.rollback_plan_id,
                "review_request_id": None,
                "created_at": created,
                "metadata_json": json.dumps(meta),
            }
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO execution_events (
                  execution_event_id, contract_id, tool_call_id, agent_id,
                  tool_name, action_type, gate_action, risk_level, status,
                  audit_event_id, rollback_plan_id, review_request_id,
                  created_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(conn_d[k] for k in (
                    "execution_event_id",
                    "contract_id",
                    "tool_call_id",
                    "agent_id",
                    "tool_name",
                    "action_type",
                    "gate_action",
                    "risk_level",
                    "status",
                    "audit_event_id",
                    "rollback_plan_id",
                    "review_request_id",
                    "created_at",
                    "metadata_json",
                )),
            )

    def create_review_request(self, request: ReviewRequest) -> None:
        self.initialize()
        now = now_utc().isoformat()
        rr = request.rde_result.model_dump(mode="json") if request.rde_result else None
        rc = request.relation_context.model_dump(mode="json") if request.relation_context else None
        rp = request.rollback_plan.model_dump(mode="json") if request.rollback_plan else None
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO review_requests (
                  review_request_id, contract_id, tool_call_id, agent_id,
                  status, reason, risk_json, rollback_plan_json,
                  rde_result_json, relation_context_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.review_request_id,
                    request.contract_id,
                    request.tool_call_id,
                    request.agent_id,
                    request.status,
                    request.reason,
                    request.risk.model_dump_json(),
                    json.dumps(rp) if rp else None,
                    json.dumps(rr) if rr else None,
                    json.dumps(rc) if rc else None,
                    request.created_at.isoformat(),
                    now,
                ),
            )

    def update_review_request_status(self, request_id: str, status: str) -> None:
        self.initialize()
        with self._connect() as conn:
            conn.execute(
                "UPDATE review_requests SET status = ?, updated_at = ? WHERE review_request_id = ?",
                (status, now_utc().isoformat(), request_id),
            )

    def append_review_decision(self, decision: ReviewDecision) -> None:
        self.initialize()
        with self._connect() as conn:
            conn.execute("BEGIN")
            try:
                conn.execute(
                    """
                    INSERT INTO review_decisions (
                      review_decision_id, review_request_id, reviewer_id,
                      decision, reason, approved_at, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        decision.review_decision_id,
                        decision.review_request_id,
                        decision.reviewer_id,
                        decision.decision,
                        decision.reason,
                        decision.approved_at.isoformat() if decision.approved_at else None,
                        decision.created_at.isoformat(),
                    ),
                )
                if decision.decision in ("approve", "approve_dry_run"):
                    st = "approved"
                elif decision.decision == "reject":
                    st = "rejected"
                elif decision.decision == "request_revision":
                    st = "revision_requested"
                elif decision.decision == "require_rollback_plan":
                    st = "pending"
                else:
                    st = "pending"
                conn.execute(
                    "UPDATE review_requests SET status = ?, updated_at = ? WHERE review_request_id = ?",
                    (st, now_utc().isoformat(), decision.review_request_id),
                )
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def save_rollback_plan(self, plan: RollbackPlan) -> None:
        self.initialize()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO rollback_plans (
                  rollback_plan_id, contract_id, strategy, target_resources_json,
                  snapshot_refs_json, reverse_patch_path, manual_steps_json,
                  validated, validation_message, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan.rollback_plan_id,
                    plan.contract_id,
                    plan.strategy,
                    json.dumps(plan.target_resources),
                    json.dumps(plan.snapshot_refs),
                    plan.reverse_patch_path,
                    json.dumps(plan.manual_steps),
                    1 if plan.validated else 0,
                    plan.validation_message,
                    plan.created_at.isoformat(),
                ),
            )
