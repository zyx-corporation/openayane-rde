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
    ev = evaluate_before_execution(
        tc,
        store,
        ExecutionPolicyConfig(),
        subject_id="s",
        object_id="o",
    )
    assert ev.decision.policy_action == "approve"
    assert ev.decision.rde_result is not None
    assert ev.decision.rde_result.evaluation_kind == "pre_synthetic"
    assert ev.decision.rde_result.evidence_basis == ["tool_risk_rule", "execution_contract"]


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
    ev = evaluate_before_execution(
        tc,
        store,
        ExecutionPolicyConfig(),
        protected_resource_paths=["secrets/"],
    )
    assert ev.decision.policy_action == "human_review"


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
    ev = evaluate_before_execution(tc, store, ExecutionPolicyConfig())
    assert ev.decision.policy_action == "halt"


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
    ev = evaluate_before_execution(
        tc,
        store,
        ExecutionPolicyConfig(allow_auto_execute_medium_risk=False),
        subject_id="s",
        object_id="o",
    )
    assert ev.decision.policy_action in ("human_review", "dry_run_only")


def test_external_read_only_fetch_human_review_without_allowlist(tmp_path) -> None:
    store = JSONRelationStore(tmp_path / "j5.json")
    tc = ToolCallRequest(
        tool_call_id="5",
        agent_id="a",
        tool_name="http_client",
        action_name="fetch",
        arguments={"method": "GET", "url": "https://example.com/data"},
        created_at=now_utc(),
    )
    ev = evaluate_before_execution(tc, store, ExecutionPolicyConfig())
    assert ev.contract.external_side_effect_kind == "read_only_fetch"
    assert ev.decision.policy_action == "human_review"


def test_external_state_changing_request_human_review(tmp_path) -> None:
    store = JSONRelationStore(tmp_path / "j6.json")
    tc = ToolCallRequest(
        tool_call_id="6",
        agent_id="a",
        tool_name="http_client",
        action_name="fetch",
        arguments={"method": "POST", "url": "https://example.com/api"},
        created_at=now_utc(),
    )
    ev = evaluate_before_execution(tc, store, ExecutionPolicyConfig())
    assert ev.contract.external_side_effect_kind == "state_changing_request"
    assert ev.decision.policy_action == "human_review"


def test_external_data_exfiltration_risk_halt(tmp_path) -> None:
    store = JSONRelationStore(tmp_path / "j7.json")
    tc = ToolCallRequest(
        tool_call_id="7",
        agent_id="a",
        tool_name="http_client",
        action_name="fetch",
        arguments={"method": "POST", "url": "https://example.com/export", "note": "upload_dump"},
        created_at=now_utc(),
    )
    ev = evaluate_before_execution(tc, store, ExecutionPolicyConfig())
    assert ev.contract.external_side_effect_kind == "data_exfiltration_risk"
    assert ev.decision.policy_action == "halt"


def test_high_risk_delete_requires_human_review_by_default(tmp_path) -> None:
    store = JSONRelationStore(tmp_path / "jd.json")
    tc = ToolCallRequest(
        tool_call_id="del1",
        agent_id="a",
        tool_name="delete_file",
        action_name="invoke",
        arguments={"path": "x.txt"},
        target_resources=["x.txt"],
        created_at=now_utc(),
    )
    ev = evaluate_before_execution(tc, store, ExecutionPolicyConfig(), subject_id="s", object_id="o")
    assert ev.decision.risk.risk_level == "high"
    assert ev.decision.policy_action == "human_review"


def test_critical_risk_human_review_when_halt_disabled(tmp_path) -> None:
    store = JSONRelationStore(tmp_path / "jc.json")
    tc = ToolCallRequest(
        tool_call_id="crit1",
        agent_id="a",
        tool_name="bash",
        action_name="invoke",
        arguments={"command": "echo", "token": "secret"},
        created_at=now_utc(),
    )
    ev = evaluate_before_execution(
        tc,
        store,
        ExecutionPolicyConfig(halt_on_critical_risk=False),
        subject_id="s",
        object_id="o",
    )
    assert ev.decision.risk.risk_level == "critical"
    assert ev.decision.policy_action == "human_review"


def test_external_unknown_human_review(tmp_path) -> None:
    store = JSONRelationStore(tmp_path / "j8.json")
    tc = ToolCallRequest(
        tool_call_id="8",
        agent_id="a",
        tool_name="http_client",
        action_name="fetch",
        arguments={"payload": "opaque-no-url-no-method"},
        created_at=now_utc(),
    )
    ev = evaluate_before_execution(tc, store, ExecutionPolicyConfig())
    assert ev.contract.external_side_effect_kind == "unknown"
    assert ev.decision.policy_action == "human_review"


def test_policy_denied_tool_halts(tmp_path) -> None:
    store = JSONRelationStore(tmp_path / "jdeny.json")
    tc = ToolCallRequest(
        tool_call_id="deny1",
        agent_id="a",
        tool_name="forbidden_plugin",
        action_name="invoke",
        arguments={"path": "x"},
        created_at=now_utc(),
    )
    ev = evaluate_before_execution(
        tc,
        store,
        ExecutionPolicyConfig(denied_tool_names=("forbidden_plugin",)),
        subject_id="s",
        object_id="o",
    )
    assert ev.decision.policy_action == "halt"
    assert ev.decision.rde_result is None


def test_policy_network_allowlist_halts_offlist_host(tmp_path) -> None:
    store = JSONRelationStore(tmp_path / "jnet.json")
    tc = ToolCallRequest(
        tool_call_id="n1",
        agent_id="a",
        tool_name="http_client",
        action_name="fetch",
        arguments={"method": "GET", "url": "https://evil.com/x"},
        created_at=now_utc(),
    )
    ev = evaluate_before_execution(
        tc,
        store,
        ExecutionPolicyConfig(network_hosts_allowlist=("example.com",)),
    )
    assert ev.decision.policy_action == "halt"
    assert "allowlist" in ev.decision.reason.lower()


def test_policy_network_allowlist_not_applied_to_filesystem(tmp_path) -> None:
    store = JSONRelationStore(tmp_path / "jfs.json")
    tc = ToolCallRequest(
        tool_call_id="f1",
        agent_id="a",
        tool_name="read_file",
        action_name="invoke",
        arguments={"path": "doc.txt"},
        created_at=now_utc(),
    )
    ev = evaluate_before_execution(
        tc,
        store,
        ExecutionPolicyConfig(network_hosts_allowlist=("example.com",)),
    )
    assert ev.decision.policy_action == "approve"


def test_evaluate_before_execution_writes_audit(tmp_path) -> None:
    from openayane_rde.audit.log import load_events

    store = JSONRelationStore(tmp_path / "jaudit.json")
    log = tmp_path / "gate.jsonl"
    tc = ToolCallRequest(
        tool_call_id="aud1",
        agent_id="a",
        tool_name="read_file",
        action_name="invoke",
        arguments={"path": "doc.txt"},
        created_at=now_utc(),
    )
    ev = evaluate_before_execution(
        tc, store, ExecutionPolicyConfig(), audit_log_path=log
    )
    assert ev.decision.audit_event_id is not None
    events = load_events(log)
    assert len(events) == 1
    assert events[0].action == "execution_gate_evaluated"
    assert events[0].payload.get("policy_action") == ev.decision.policy_action
