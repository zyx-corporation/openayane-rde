"""Integration: tool call → gate → runtime (Phase 3)."""

from __future__ import annotations

from pathlib import Path

from openayane_rde.agent.execution_gate import (
    enforce_execution_decision,
    evaluate_before_execution,
    execute_after_review_decision,
)
from openayane_rde.audit.log import (
    append_audit_event,
    audit_event_execution_gate_evaluated,
    audit_event_human_review_decided,
    audit_event_tool_execution,
)
from openayane_rde.core.models import (
    ReviewDecision,
    ReviewRequest,
    ToolCallRequest,
    ToolExecutionResult,
)
from openayane_rde.core.time import now_utc
from openayane_rde.policy.execution_rules import ExecutionPolicyConfig
from openayane_rde.relation.sqlite_store import SQLiteRelationStore
from openayane_rde.review.workflow import HumanReviewWorkflow
from openayane_rde.runtime.safe_execution import SafeExecutionRuntime


def test_gate_to_sqlite_event(tmp_path: Path) -> None:
    db = tmp_path / "db.sqlite3"
    store = SQLiteRelationStore(db)
    store.initialize()
    tc = ToolCallRequest(
        tool_call_id="tc1",
        agent_id="agent",
        tool_name="read_file",
        action_name="invoke",
        arguments={"path": "hello.txt"},
        created_at=now_utc(),
    )
    ev = evaluate_before_execution(
        tc,
        store,
        ExecutionPolicyConfig(),
        subject_id="agent",
        object_id="ws",
    )
    gate, contract = ev.decision, ev.contract
    wf = HumanReviewWorkflow(store)
    rt = SafeExecutionRuntime(tmp_path)
    (tmp_path / "hello.txt").write_text("x", encoding="utf-8")
    out = enforce_execution_decision(gate, rt, wf, tool_call=tc, contract=contract)
    assert isinstance(out, ToolExecutionResult)
    assert out.status == "completed"
    store.append_execution_event(
        gate,
        agent_id=tc.agent_id,
        tool_name=tc.tool_name,
        tool_call_id=tc.tool_call_id,
        action_type=contract.action_type,
    )


def test_human_review_approve_dry_run_then_runtime(tmp_path: Path) -> None:
    db = tmp_path / "db.sqlite3"
    store = SQLiteRelationStore(db)
    store.initialize()
    audit_log = tmp_path / "audit.jsonl"
    tc = ToolCallRequest(
        tool_call_id="tc-hr",
        agent_id="agent",
        tool_name="write_file",
        action_name="invoke",
        arguments={"path": "out/x.txt", "content": "y"},
        target_resources=["out/x.txt"],
        created_at=now_utc(),
    )
    ev = evaluate_before_execution(
        tc,
        store,
        ExecutionPolicyConfig(),
        subject_id="agent",
        object_id="ws",
        protected_resource_paths=["out/"],
    )
    gate, contract = ev.decision, ev.contract
    assert gate.policy_action == "human_review"

    ge = audit_event_execution_gate_evaluated(gate, tool_call_id=tc.tool_call_id)
    append_audit_event(audit_log, ge)
    gate = gate.model_copy(update={"audit_event_id": ge.event_id})

    wf = HumanReviewWorkflow(store)
    rt = SafeExecutionRuntime(tmp_path)
    (tmp_path / "out").mkdir(parents=True, exist_ok=True)
    pending = enforce_execution_decision(gate, rt, wf, tool_call=tc, contract=contract)
    assert isinstance(pending, ReviewRequest)

    rv = ReviewDecision(
        review_request_id=pending.review_request_id,
        reviewer_id="rev1",
        decision="approve_dry_run",
        reason="ok",
    )
    hd = audit_event_human_review_decided(rv, request=pending)
    append_audit_event(audit_log, hd)

    resumed = execute_after_review_decision(
        decision=rv,
        contract=contract,
        tool_call=tc,
        runtime=rt,
    )
    assert resumed is not None
    assert resumed.status == "dry_run_completed"
    te = audit_event_tool_execution(
        resumed,
        "execution_dry_run_completed",
        explanation="dry-run after review",
    )
    append_audit_event(audit_log, te)
    resumed = resumed.model_copy(update={"audit_event_id": te.event_id})

    store.append_execution_event(
        gate,
        agent_id=tc.agent_id,
        tool_name=tc.tool_name,
        tool_call_id=tc.tool_call_id,
        action_type=contract.action_type,
    )
    store.append_execution_event(
        resumed,
        agent_id=tc.agent_id,
        tool_name=tc.tool_name,
        action_type=contract.action_type,
    )

    target = tmp_path / "out" / "x.txt"
    assert not target.exists()

    from openayane_rde.audit.log import load_events

    events = load_events(audit_log)
    kinds = [e.payload.get("evaluation_kind") for e in events if e.action == "execution_gate_evaluated"]
    assert kinds == ["pre_synthetic"]
    basis = [e.payload.get("evidence_basis") for e in events if e.action == "execution_gate_evaluated"]
    assert basis == [["tool_risk_rule", "execution_contract"]]


def test_denied_tool_blocked_and_audit_logged(tmp_path: Path) -> None:
    db = tmp_path / "db.sqlite3"
    store = SQLiteRelationStore(db)
    store.initialize()
    audit_log = tmp_path / "audit.jsonl"
    tc = ToolCallRequest(
        tool_call_id="tc-block",
        agent_id="agent",
        tool_name="forbidden_plugin",
        action_name="invoke",
        arguments={"path": "p"},
        created_at=now_utc(),
    )
    cfg = ExecutionPolicyConfig(denied_tool_names=("forbidden_plugin",))
    ev = evaluate_before_execution(
        tc,
        store,
        cfg,
        subject_id="agent",
        object_id="ws",
        audit_log_path=audit_log,
    )
    assert ev.decision.policy_action == "halt"
    assert ev.decision.audit_event_id is not None

    wf = HumanReviewWorkflow(store)
    rt = SafeExecutionRuntime(tmp_path)
    out = enforce_execution_decision(ev.decision, rt, wf, tool_call=tc, contract=ev.contract)
    assert isinstance(out, ToolExecutionResult)
    assert out.status == "blocked"

    from openayane_rde.audit.log import load_events

    rows = load_events(audit_log)
    assert rows[0].action == "execution_gate_evaluated"
    assert rows[0].payload.get("policy_action") == "halt"
