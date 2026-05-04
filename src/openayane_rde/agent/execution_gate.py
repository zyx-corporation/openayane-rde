"""Agent execution gate — evaluate tool calls before execution (Phase 3)."""

from __future__ import annotations

from openayane_rde.agent.tool_contract import (
    build_execution_task_contract,
    score_tool_call_risk,
)
from openayane_rde.core.models import (
    ExecutionGateDecision,
    ExecutionTaskContract,
    ReviewRequest,
    ToolCallRequest,
    ToolExecutionResult,
)
from openayane_rde.policy.execution_rules import (
    ExecutionPolicyConfig,
    decide_execution_policy_action,
    synthetic_rde_for_tool,
)
from openayane_rde.relation.store import RelationStore
from openayane_rde.review.workflow import HumanReviewWorkflow
from openayane_rde.runtime.safe_execution import SafeExecutionRuntime


def evaluate_before_execution(
    tool_call: ToolCallRequest,
    relation_store: RelationStore,
    policy_config: ExecutionPolicyConfig,
    *,
    subject_id: str = "unknown",
    object_id: str = "unknown",
    relation_type: str = "generator-document",
    protected_resource_paths: list[str] | None = None,
) -> tuple[ExecutionGateDecision, ExecutionTaskContract]:
    """Run contract building, risk scoring, synthetic RDE, and policy.

    Returns the gate decision together with the :class:`ExecutionTaskContract`
    instance so callers can pass the same object to :func:`enforce_execution_decision`.
    """

    contract = build_execution_task_contract(tool_call)
    risk = score_tool_call_risk(
        contract,
        protected_resource_paths=protected_resource_paths,
        raw_arguments=tool_call.arguments,
    )
    rde = synthetic_rde_for_tool(contract.contract_id, risk)
    rc = relation_store.load_context(subject_id, object_id, relation_type)
    action, reason = decide_execution_policy_action(risk, rde, rc, policy_config)
    gate = ExecutionGateDecision(
        contract_id=contract.contract_id,
        policy_action=action,
        reason=reason,
        risk=risk,
        rde_result=rde,
        relation_context=rc,
    )
    return gate, contract


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
