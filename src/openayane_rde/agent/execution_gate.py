"""Agent execution gate — evaluate tool calls before execution (Phase 3)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, assert_never
from urllib.parse import urlparse

from openayane_rde.agent.tool_contract import (
    _URL_KEYS,
    _first_str,
    build_execution_task_contract,
    score_tool_call_risk,
)
from openayane_rde.audit.log import append_audit_event, audit_event_execution_gate_evaluated
from openayane_rde.core.models import (
    ExecutionGateDecision,
    ExecutionGateEvaluation,
    ExecutionTaskContract,
    RelationContext,
    ReviewDecision,
    ReviewRequest,
    RollbackPlan,
    ToolCallRequest,
    ToolCallRisk,
    ToolExecutionResult,
)
from openayane_rde.institution.pop_uid import PopUidAdapter
from openayane_rde.institution.rule_registry import InstitutionRuleRegistry
from openayane_rde.policy.execution_rules import (
    ExecutionPolicyConfig,
    apply_relation_history_to_execution_gate,
    decide_execution_policy_action,
    synthetic_rde_for_tool,
)
from openayane_rde.relation.store import RelationStore
from openayane_rde.review.workflow import HumanReviewWorkflow
from openayane_rde.runtime.safe_execution import SafeExecutionRuntime

PostReviewExecutionMode = Literal[
    "full_execute",
    "dry_run_only",
    "denied",
    "pending_more",
]


def post_review_execution_mode(decision: ReviewDecision) -> PostReviewExecutionMode:
    """Map a reviewer decision to the safe-runtime path (policy outcome after review)."""

    d = decision.decision
    if d == "approve":
        return "full_execute"
    if d == "approve_dry_run":
        return "dry_run_only"
    if d == "reject":
        return "denied"
    if d == "request_revision":
        return "pending_more"
    if d == "require_rollback_plan":
        return "pending_more"
    assert_never(d)


def _url_host_matches_allowlist(url: str, hosts: tuple[str, ...]) -> bool:
    host = (urlparse(url).hostname or "").lower()
    if not host:
        return False
    return any(host == d.lower() or host.endswith(f".{d.lower()}") for d in hosts)


def _network_allowlist_allows(
    contract: ExecutionTaskContract,
    tool_call: ToolCallRequest,
    policy_hosts: tuple[str, ...],
) -> tuple[bool, str]:
    if not policy_hosts:
        return True, ""
    if contract.action_type not in ("network", "external_api"):
        return True, ""
    url = _first_str(tool_call.arguments, _URL_KEYS)
    if not url:
        return False, "Policy network allowlist is active; the tool call must include a URL."
    if not _url_host_matches_allowlist(url, policy_hosts):
        return False, "Network host is not on the policy allowlist."
    return True, ""


def _policy_halt_decision(
    contract: ExecutionTaskContract,
    relation_context: RelationContext,
    reason: str,
    *,
    external: bool,
) -> ExecutionGateDecision:
    risk = ToolCallRisk(
        risk_level="high",
        risk_score=0.88,
        irreversible=False,
        external_side_effect=external,
        protected_resource_touched=False,
        rollback_possible=True,
        unknown_target=False,
        reasons=["policy_gate"],
    )
    return ExecutionGateDecision(
        contract_id=contract.contract_id,
        policy_action="halt",
        reason=reason,
        risk=risk,
        rde_result=None,
        relation_context=relation_context,
    )


def _evaluation_with_audit(
    evaluation: ExecutionGateEvaluation,
    tool_call: ToolCallRequest,
    audit_log_path: str | Path | None,
) -> ExecutionGateEvaluation:
    if audit_log_path is None:
        return evaluation
    ae = audit_event_execution_gate_evaluated(
        evaluation.decision,
        tool_call_id=tool_call.tool_call_id,
    )
    append_audit_event(audit_log_path, ae)
    gate = evaluation.decision.model_copy(update={"audit_event_id": ae.event_id})
    return ExecutionGateEvaluation(decision=gate, contract=evaluation.contract)


def _apply_institution_to_execution_gate(
    contract: ExecutionTaskContract,
    gate: ExecutionGateDecision,
    *,
    institution_registry: InstitutionRuleRegistry | None,
    pop_verifier: PopUidAdapter | None,
    pop_subject_id: str | None,
) -> ExecutionGateDecision:
    """Optional Phase 4 overlay: PoP check for critical RDE risk, :class:`InstitutionRule` escalation."""

    g = gate
    rde = g.rde_result

    if pop_verifier is not None and pop_subject_id is not None and rde is not None:
        if rde.risk_level == "critical" and not pop_verifier.has_valid_pop(
            pop_subject_id
        ):
            if g.policy_action != "halt":
                inst = (
                    "PoP-UID / institutional identity could not be verified; "
                    "critical path halted by institution policy."
                )
                return g.model_copy(
                    update={
                        "policy_action": "halt",
                        "reason": f"{g.reason} [Institution] {inst}",
                        "institutional_rationale": inst,
                    }
                )

    if institution_registry is None:
        return g

    rule = institution_registry.first_match(
        action_type=contract.action_type,
        side_effect=contract.external_side_effect_kind,
    )
    if rule is None:
        return g

    inst_parts: list[str] = []
    new_action = g.policy_action
    if rule.requires_human_review and new_action in (
        "approve",
        "approve_with_notes",
        "dry_run_only",
    ):
        new_action = "human_review"
        inst_parts.append(
            f"InstitutionRule {rule.rule_id} requires human review before execution."
        )
    if rule.requires_rollback_plan:
        inst_parts.append(
            f"InstitutionRule {rule.rule_id} requires a recorded rollback plan."
        )

    inst_text = " ".join(inst_parts) if inst_parts else None
    if new_action == g.policy_action and inst_text is None:
        return g

    new_reason = g.reason
    if inst_text:
        new_reason = f"{g.reason} [Institution] {inst_text}"
    notes = list(g.policy_adjustment_notes)
    if inst_text:
        notes.append(inst_text)
    return g.model_copy(
        update={
            "policy_action": new_action,
            "reason": new_reason,
            "institution_rule_id": rule.rule_id,
            "institutional_rationale": inst_text,
            "policy_adjustment_notes": notes,
        }
    )


def evaluate_before_execution(
    tool_call: ToolCallRequest,
    relation_store: RelationStore,
    policy_config: ExecutionPolicyConfig,
    *,
    subject_id: str = "unknown",
    object_id: str = "unknown",
    relation_type: str = "generator-document",
    protected_resource_paths: list[str] | None = None,
    audit_log_path: str | Path | None = None,
    institution_registry: InstitutionRuleRegistry | None = None,
    pop_verifier: PopUidAdapter | None = None,
    pop_subject_id: str | None = None,
) -> ExecutionGateEvaluation:
    """Run contract building, risk scoring, synthetic RDE, and policy.

    Optional ``denied_tool_names`` / ``network_hosts_allowlist`` on
    :class:`~openayane_rde.policy.execution_rules.ExecutionPolicyConfig` run before
    risk scoring. When ``audit_log_path`` is set, appends ``execution_gate_evaluated``
    and sets :attr:`~openayane_rde.core.models.ExecutionGateDecision.audit_event_id`.

    Optional Phase 4: ``institution_registry`` applies :class:`InstitutionRule` escalation
    after the execution policy path; ``pop_verifier`` / ``pop_subject_id`` can force halt
    when :class:`RDEResult` has ``risk_level == "critical"`` and PoP fails.

    Returns an :class:`ExecutionGateEvaluation` bundling the gate decision and
    :class:`ExecutionTaskContract` for :func:`enforce_execution_decision`.
    """

    contract = build_execution_task_contract(tool_call)
    rc = relation_store.load_context(subject_id, object_id, relation_type)

    if policy_config.denied_tool_names and tool_call.tool_name in policy_config.denied_tool_names:
        gate = _policy_halt_decision(
            contract,
            rc,
            "Tool blocked by policy denylist.",
            external=contract.action_type in ("network", "external_api"),
        )
        return _evaluation_with_audit(
            ExecutionGateEvaluation(decision=gate, contract=contract),
            tool_call,
            audit_log_path,
        )

    net_ok, net_msg = _network_allowlist_allows(
        contract,
        tool_call,
        policy_config.network_hosts_allowlist,
    )
    if not net_ok:
        gate = _policy_halt_decision(
            contract,
            rc,
            net_msg,
            external=True,
        )
        return _evaluation_with_audit(
            ExecutionGateEvaluation(decision=gate, contract=contract),
            tool_call,
            audit_log_path,
        )

    risk = score_tool_call_risk(
        contract,
        protected_resource_paths=protected_resource_paths,
        raw_arguments=tool_call.arguments,
    )
    rde = synthetic_rde_for_tool(contract.contract_id, risk)
    rde = rde.model_copy(
        update={
            "metadata": {
                **rde.metadata,
                "external_side_effect_kind": contract.external_side_effect_kind,
            }
        }
    )
    action, reason = decide_execution_policy_action(risk, rde, rc, policy_config)
    adjusted, bridge_notes = apply_relation_history_to_execution_gate(action, rc)
    merged_reason = reason
    if bridge_notes:
        merged_reason = f"{reason} | {' '.join(bridge_notes)}"
    gate = ExecutionGateDecision(
        contract_id=contract.contract_id,
        policy_action=adjusted,
        reason=merged_reason,
        risk=risk,
        rde_result=rde,
        relation_context=rc,
        policy_adjustment_notes=bridge_notes,
    )
    gate = _apply_institution_to_execution_gate(
        contract,
        gate,
        institution_registry=institution_registry,
        pop_verifier=pop_verifier,
        pop_subject_id=pop_subject_id,
    )
    return _evaluation_with_audit(
        ExecutionGateEvaluation(decision=gate, contract=contract),
        tool_call,
        audit_log_path,
    )


def enforce_execution_decision(
    gate: ExecutionGateDecision,
    runtime: SafeExecutionRuntime,
    review_workflow: HumanReviewWorkflow,
    *,
    tool_call: ToolCallRequest,
    contract: ExecutionTaskContract,
) -> ToolExecutionResult | ReviewRequest:
    """Dispatch to review queue, block, or safe runtime."""

    if gate.policy_action == "halt":
        return ToolExecutionResult(
            contract_id=contract.contract_id,
            tool_call_id=tool_call.tool_call_id,
            status="blocked",
            stderr=gate.reason,
            error_message="halt",
        )

    if gate.policy_action == "human_review":
        return review_workflow.create_request(
            gate,
            contract,
            tool_call_id=tool_call.tool_call_id,
            agent_id=tool_call.agent_id,
        )

    dry_run = gate.policy_action == "dry_run_only"
    if gate.policy_action in ("approve", "approve_with_notes", "dry_run_only"):
        return runtime.execute(contract, tool_call, dry_run=dry_run)

    return ToolExecutionResult(
        contract_id=contract.contract_id,
        tool_call_id=tool_call.tool_call_id,
        status="not_executed",
        stderr=f"Unhandled gate action: {gate.policy_action}",
    )


def execute_after_review_decision(
    *,
    decision: ReviewDecision,
    contract: ExecutionTaskContract,
    tool_call: ToolCallRequest,
    runtime: SafeExecutionRuntime,
    rollback_plan: RollbackPlan | None = None,
) -> ToolExecutionResult | None:
    """Run the safe runtime after a reviewer approves execution or dry-run only."""

    if decision.decision == "approve_dry_run":
        return runtime.execute(contract, tool_call, rollback_plan, dry_run=True)
    if decision.decision == "approve":
        return runtime.execute(contract, tool_call, rollback_plan, dry_run=False)
    return None
