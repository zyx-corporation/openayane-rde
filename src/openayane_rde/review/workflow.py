"""Human review workflow (Phase 3)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from openayane_rde.audit.log import (
    append_audit_event,
    audit_event_human_review_decided,
    audit_event_human_review_requested,
)
from openayane_rde.core.models import (
    ExecutionGateDecision,
    ExecutionTaskContract,
    ReviewDecision,
    ReviewRequest,
)

if TYPE_CHECKING:
    from openayane_rde.relation.sqlite_store import SQLiteRelationStore


class HumanReviewWorkflow:
    """In-memory queue with optional SQLite backing and optional JSONL audit log."""

    def __init__(
        self,
        store: SQLiteRelationStore | None = None,
        *,
        audit_log_path: str | Path | None = None,
    ) -> None:
        self._store = store
        self._audit_log_path: Path | None = (
            Path(audit_log_path) if audit_log_path is not None else None
        )
        self._by_id: dict[str, ReviewRequest] = {}

    def create_request(
        self,
        gate: ExecutionGateDecision,
        contract: ExecutionTaskContract,
        *,
        tool_call_id: str,
        agent_id: str,
    ) -> ReviewRequest:
        req = ReviewRequest(
            contract_id=contract.contract_id,
            tool_call_id=tool_call_id,
            agent_id=agent_id,
            reason=gate.reason,
            risk=gate.risk,
            proposed_action_summary=f"{contract.action_type}:{contract.tool_name}",
            expected_side_effects=contract.expected_side_effects,
            forbidden_side_effects=contract.forbidden_side_effects,
            rde_result=gate.rde_result,
            relation_context=gate.relation_context,
            status="pending",
        )
        self._by_id[req.review_request_id] = req
        if self._store is not None:
            self._store.create_review_request(req)
        if self._audit_log_path is not None:
            ev = audit_event_human_review_requested(req)
            append_audit_event(self._audit_log_path, ev)
        return req

    def submit_decision(self, decision: ReviewDecision) -> ReviewRequest | None:
        req = self._by_id.get(decision.review_request_id)
        if req is None:
            return None
        if decision.decision in ("approve", "approve_dry_run"):
            new_status = "approved"
        elif decision.decision == "reject":
            new_status = "rejected"
        elif decision.decision == "request_revision":
            new_status = "revision_requested"
        elif decision.decision == "require_rollback_plan":
            new_status = "pending"
        else:
            new_status = req.status
        updated = req.model_copy(update={"status": new_status})
        self._by_id[decision.review_request_id] = updated
        if self._store is not None:
            self._store.append_review_decision(decision)
        if self._audit_log_path is not None:
            ev = audit_event_human_review_decided(decision, request=req)
            append_audit_event(self._audit_log_path, ev)
        return updated

    def get_pending(self) -> list[ReviewRequest]:
        return [r for r in self._by_id.values() if r.status == "pending"]

    def get(self, review_request_id: str) -> ReviewRequest | None:
        return self._by_id.get(review_request_id)
