"""Append-only JSONL AuditLog writer and reader for OpenAyane RDE."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from openayane_rde.core.errors import AuditError
from openayane_rde.core.models import (
    AuditActionKind,
    AuditEvent,
    ExecutionGateDecision,
    PolicyDecision,
    ReviewDecision,
    ReviewRequest,
    RollbackPlan,
    RollbackResult,
    ToolExecutionResult,
)

AuditActionExecution = Literal[
    "execution_blocked",
    "execution_approved",
    "execution_dry_run_completed",
    "execution_completed",
    "execution_failed",
    "execution_timed_out",
]


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


def audit_event_execution_gate_evaluated(
    gate: ExecutionGateDecision,
    *,
    tool_call_id: str,
) -> AuditEvent:
    """Uniform audit row for a pre-execution gate outcome."""

    eval_kind = gate.rde_result.evaluation_kind if gate.rde_result else None
    return AuditEvent(
        actor="policy",
        action="execution_gate_evaluated",
        task_contract_id=gate.contract_id,
        rde_result_id=gate.rde_result.result_id if gate.rde_result else None,
        explanation=gate.reason,
        payload={
            "decision_id": gate.decision_id,
            "contract_id": gate.contract_id,
            "tool_call_id": tool_call_id,
            "policy_action": gate.policy_action,
            "evaluation_kind": eval_kind,
            "evidence_basis": gate.rde_result.evidence_basis if gate.rde_result else [],
            "risk_level": gate.risk.risk_level,
            "gating_rationale": gate.policy_adjustment_notes,
            "institution_rule_id": gate.institution_rule_id,
            "institutional_rationale": gate.institutional_rationale,
        },
    )


def audit_event_tool_execution(
    result: ToolExecutionResult,
    action: AuditActionExecution,
    *,
    explanation: str,
) -> AuditEvent:
    """Uniform audit row for safe-runtime outcomes."""

    return AuditEvent(
        actor="runtime",
        action=action,
        task_contract_id=result.contract_id,
        execution_result_id=result.execution_id,
        explanation=explanation,
        payload={
            "contract_id": result.contract_id,
            "tool_call_id": result.tool_call_id,
            "status": result.status,
            "error_message": result.error_message,
        },
    )


def audit_event_human_review_requested(request: ReviewRequest) -> AuditEvent:
    return AuditEvent(
        actor="policy",
        action="human_review_requested",
        task_contract_id=request.contract_id,
        explanation=request.reason,
        payload={
            "review_request_id": request.review_request_id,
            "contract_id": request.contract_id,
            "tool_call_id": request.tool_call_id,
            "agent_id": request.agent_id,
            "risk_level": request.risk.risk_level,
        },
    )


def audit_event_human_review_decided(
    decision: ReviewDecision,
    *,
    request: ReviewRequest | None = None,
) -> AuditEvent:
    return AuditEvent(
        actor="reviewer",
        action="human_review_decided",
        task_contract_id=request.contract_id if request else None,
        explanation=decision.reason,
        payload={
            "review_decision_id": decision.review_decision_id,
            "review_request_id": decision.review_request_id,
            "decision": decision.decision,
            "reviewer_id": decision.reviewer_id,
        },
    )


def audit_event_rollback_executed(
    plan: RollbackPlan,
    result: RollbackResult,
    *,
    trigger_reason: str = "",
) -> AuditEvent:
    """Audit row after :meth:`~openayane_rde.runtime.rollback.RollbackManager.execute_rollback`."""

    action: AuditActionKind = (
        "rollback_completed" if result.status == "completed" else "rollback_failed"
    )
    expl = trigger_reason.strip() or f"Rollback finished with status {result.status}."
    return AuditEvent(
        actor="runtime",
        action=action,
        task_contract_id=plan.contract_id,
        explanation=expl,
        payload={
            "rollback_plan_id": plan.rollback_plan_id,
            "rollback_result_id": result.rollback_result_id,
            "rollback_result_status": result.status,
            "strategy": plan.strategy,
            "restored_resources": result.restored_resources,
            "error_message": result.error_message,
        },
    )


def append_audit_event(path: str | Path, event: AuditEvent) -> AuditEvent:
    """Append and return the same event (for chaining IDs onto domain objects)."""

    append_event(path, event)
    return event


def audit_event_policy_decision(
    decision: PolicyDecision,
    *,
    rde_classification: str,
) -> AuditEvent:
    """Append-only shape for policy decisions with explicit RDE vs institution payload split."""

    return AuditEvent(
        actor="policy",
        action="make_policy_decision",
        task_contract_id=decision.contract_id,
        rde_result_id=decision.rde_result_id,
        policy_decision_id=decision.decision_id,
        explanation=decision.rationale,
        payload={
            "policy_action": decision.action,
            "rde_classification": rde_classification,
            "institution_rule_id": decision.institution_rule_id,
            "institutional_rationale": decision.institutional_rationale,
            "layer_note": (
                "rde_result carries semantic classification; institution_rule_id binds "
                "organizational rules without replacing RDE."
            ),
        },
    )
