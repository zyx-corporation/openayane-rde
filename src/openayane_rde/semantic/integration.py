"""Optional Semantic Evaluator integration seam (Phase 3).

Call sites pass ``evaluator=None`` to preserve default structural / gate behaviour.
When an evaluator is supplied, results are advisory inputs alongside RDE and policy,
not a replacement for institutional judgement.

See :class:`~openayane_rde.semantic.evaluator.SemanticEvaluator` and module docs there.
"""

from __future__ import annotations

from openayane_rde.core.models import (
    ExecutionTaskContract,
    PostExecutionDiff,
    RelationContext,
    SemanticEvaluationResult,
    ToolCallRequest,
    ToolExecutionResult,
)
from openayane_rde.semantic.evaluator import SemanticEvaluator


def optional_evaluate_execution_intent(
    evaluator: SemanticEvaluator | None,
    contract: ExecutionTaskContract,
    tool_call: ToolCallRequest,
    relation_context: RelationContext | None = None,
) -> SemanticEvaluationResult | None:
    """Run pre-execution semantic assist when an evaluator is configured."""

    if evaluator is None:
        return None
    return evaluator.evaluate_execution_intent(
        contract,
        tool_call,
        relation_context=relation_context,
    )


def optional_evaluate_post_execution(
    evaluator: SemanticEvaluator | None,
    contract: ExecutionTaskContract,
    result: ToolExecutionResult,
    post_diff: PostExecutionDiff,
) -> SemanticEvaluationResult | None:
    """Run post-execution semantic assist when an evaluator is configured."""

    if evaluator is None:
        return None
    return evaluator.evaluate_post_execution(contract, result, post_diff)
