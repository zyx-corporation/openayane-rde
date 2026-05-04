"""Execution gate (Phase 3)."""

from __future__ import annotations

from openayane_rde.agent.execution_gate import evaluate_before_execution
from openayane_rde.core.models import ToolCallRequest
from openayane_rde.core.time import now_utc
from openayane_rde.policy.execution_rules import ExecutionPolicyConfig
from openayane_rde.relation.store import JSONRelationStore


def test_low_risk_read_approve(tmp_path) -> None:
    store = JSONRelationStore(tmp_path / "j.json")
    tc = ToolCallRequest(
        tool_call_id="1",
        agent_id="a",
        tool_name="read_file",
        action_name="invoke",
        arguments={"path": "doc.txt"},
        created_at=now_utc(),
    )
    gate, _ = evaluate_before_execution(
        tc,
        store,
        ExecutionPolicyConfig(),
        subject_id="s",
        object_id="o",
    )
    assert gate.policy_action == "approve"


def test_protected_resource_human_review(tmp_path) -> None:
    store = JSONRelationStore(tmp_path / "j2.json")
    tc = ToolCallRequest(
        tool_call_id="2",
        agent_id="a",
        tool_name="write",
        action_name="invoke",
        arguments={"path": "secrets/x", "content": "1"},
        created_at=now_utc(),
    )
    gate, _ = evaluate_before_execution(
        tc,
        store,
        ExecutionPolicyConfig(),
        protected_resource_paths=["secrets/"],
    )
    assert gate.policy_action == "human_review"


def test_secret_access_halt(tmp_path) -> None:
    store = JSONRelationStore(tmp_path / "j3.json")
    tc = ToolCallRequest(
        tool_call_id="3",
        agent_id="a",
        tool_name="bash",
        action_name="invoke",
        arguments={"command": "echo", "token": "abc"},
        created_at=now_utc(),
    )
    gate, _ = evaluate_before_execution(tc, store, ExecutionPolicyConfig())
    assert gate.policy_action == "halt"


def test_low_trust_medium_write_human_review(tmp_path) -> None:
    store = JSONRelationStore(tmp_path / "j4.json")
    from openayane_rde.core.models import RelationStoreRecord

    store.upsert(
        RelationStoreRecord(
            subject_id="s",
            object_id="o",
            trust=0.2,
            stability=0.5,
        )
    )
    tc = ToolCallRequest(
        tool_call_id="4",
        agent_id="a",
        tool_name="write_file",
        action_name="invoke",
        arguments={"path": "f.txt", "content": "x"},
        created_at=now_utc(),
    )
    gate, contract = evaluate_before_execution(
        tc,
        store,
        ExecutionPolicyConfig(allow_auto_execute_medium_risk=False),
        subject_id="s",
        object_id="o",
    )
    assert gate.policy_action in ("human_review", "dry_run_only")
