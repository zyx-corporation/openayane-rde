"""Policy Bridge: converts RDEResult into PolicyDecision.

Initial mapping:
  preserved + low risk -> approve
  authorized_deviation -> approve_with_notes
  suspicious_drift -> human_review
  critical_corruption -> halt
"""

from __future__ import annotations

from openayane_rde.core.models import PolicyDecision, RelationContext, RDEResult, TaskContract
from openayane_rde.policy.rules import decide_action


def decide_policy(
    rde_result: RDEResult,
    contract: TaskContract,
    relation_context: RelationContext | None = None,
) -> PolicyDecision:
    """Convert RDEResult into a PolicyDecision.

    critical_corruption classification always results in halt.
    Other classifications use the review_policy from the TaskContract.
    """
    action = decide_action(rde_result, contract, relation_context)
    rationale = _build_rationale(rde_result, action)

    return PolicyDecision(
        contract_id=contract.contract_id,
        rde_result_id=rde_result.result_id,
        action=action,
        rationale=rationale,
    )


def _build_rationale(rde_result: RDEResult, action: str) -> str:
    parts = [
        f"RDE classification: {rde_result.classification}.",
        f"Risk level: {rde_result.risk_level}.",
        f"Policy action: {action}.",
    ]

    if rde_result.violated_constraints:
        n = len(rde_result.violated_constraints)
        parts.append(f"{n} constraint violation(s) detected.")

    if rde_result.suspicious_elements:
        n = len(rde_result.suspicious_elements)
        parts.append(f"{n} suspicious element(s) identified.")

    if action == "halt":
        parts.append(
            "Change application halted. Critical corruption must not be auto-applied."
        )
    elif action == "human_review":
        parts.append(
            "Human review required before change can be applied."
        )
    elif action == "approve_with_notes":
        parts.append("Change approved with review notes attached.")
    elif action == "approve":
        parts.append("Change approved automatically.")

    return " ".join(parts)
