"""Optional semantic evaluator (rule-based + LLM stub) for Phase 3."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from openayane_rde.core.models import (
    ExecutionTaskContract,
    PostExecutionDiff,
    RelationContext,
    SemanticEvaluationResult,
    SemanticEvaluatorRecommendation,
    ToolCallRequest,
    ToolExecutionResult,
)


@runtime_checkable
class SemanticEvaluator(Protocol):
    """Pluggable semantic assist (not the sole RDE authority)."""

    def evaluate_execution_intent(
        self,
        contract: ExecutionTaskContract,
        tool_call: ToolCallRequest,
        relation_context: RelationContext | None = None,
    ) -> SemanticEvaluationResult:
        ...

    def evaluate_post_execution(
        self,
        contract: ExecutionTaskContract,
        result: ToolExecutionResult,
        post_diff: PostExecutionDiff,
    ) -> SemanticEvaluationResult:
        ...


class RuleBasedSemanticEvaluator:
    """Heuristic checks on purpose, side effects, and protected resources."""

    def evaluate_execution_intent(
        self,
        contract: ExecutionTaskContract,
        tool_call: ToolCallRequest,
        relation_context: RelationContext | None = None,
    ) -> SemanticEvaluationResult:
        issues: list[str] = []
        if tool_call.declared_purpose:
            p = tool_call.declared_purpose.lower()
            if "read" in p and contract.action_type != "read":
                issues.append("declared_purpose vs action_type mismatch")
        overlap = set(contract.expected_side_effects) & set(contract.forbidden_side_effects)
        if overlap:
            issues.append(f"expected/forbidden overlap: {overlap}")
        if contract.protected_resources and not tool_call.agent_self_report:
            issues.append("missing agent self-report for protected resource context")
        if contract.action_type in ("network", "external_api") and not tool_call.declared_purpose:
            issues.append("external action without declared purpose")
        rec: SemanticEvaluatorRecommendation = "no_issue"
        if issues:
            rec = "human_review"
        return SemanticEvaluationResult(
            confidence=0.6 if issues else 0.9,
            suspected_delta_m=issues,
            drift_risks=issues,
            recommendation=rec,
            explanation="; ".join(issues) if issues else "Rule-based checks passed.",
        )

    def evaluate_post_execution(
        self,
        contract: ExecutionTaskContract,
        result: ToolExecutionResult,
        post_diff: PostExecutionDiff,
    ) -> SemanticEvaluationResult:
        issues: list[str] = []
        if post_diff.unexpected_side_effects:
            issues.extend(post_diff.unexpected_side_effects)
        rec: SemanticEvaluatorRecommendation = "no_issue" if not issues else "approve_with_notes"
        return SemanticEvaluationResult(
            confidence=0.55,
            suspected_delta_m=issues,
            drift_risks=issues,
            recommendation=rec,
            explanation="Post-execution rule scan.",
        )


class LLMSemanticEvaluatorStub:
    """Placeholder for a future LLM-backed evaluator."""

    def evaluate_execution_intent(
        self,
        contract: ExecutionTaskContract,
        tool_call: ToolCallRequest,
        relation_context: RelationContext | None = None,
    ) -> SemanticEvaluationResult:
        return SemanticEvaluationResult(
            confidence=0.0,
            explanation="LLM semantic evaluator not configured (stub).",
            recommendation="human_review",
        )

    def evaluate_post_execution(
        self,
        contract: ExecutionTaskContract,
        result: ToolExecutionResult,
        post_diff: PostExecutionDiff,
    ) -> SemanticEvaluationResult:
        return SemanticEvaluationResult(
            confidence=0.0,
            explanation="LLM semantic evaluator not configured (stub).",
            recommendation="human_review",
        )
