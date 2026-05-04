"""Modification Control Flow for Phase 1.

Phase 1: no real file modification by default.
Returns would-apply / halt / pending-review result.
"""

from __future__ import annotations

from openayane_rde.core.models import ModificationOutcome, PolicyDecision, TaskContract


def apply_or_halt(
    contract: TaskContract,
    policy_decision: PolicyDecision,
) -> ModificationOutcome:
    """Determine whether to apply a change based on PolicyDecision.

    Phase 1: does not write files. Returns a ModificationOutcome indicating outcome.
    """
    action = policy_decision.action

    if action == "halt":
        return ModificationOutcome(
            contract_id=contract.contract_id,
            policy_decision_id=policy_decision.decision_id,
            outcome="halted",
            explanation=(
                "Change halted by Policy Bridge. "
                "Critical corruption must not be auto-applied."
            ),
        )

    if action in ("human_review", "request_revision"):
        return ModificationOutcome(
            contract_id=contract.contract_id,
            policy_decision_id=policy_decision.decision_id,
            outcome="pending_review",
            explanation=(
                f"Change pending human review. Policy action: {action}."
            ),
        )

    if action in ("approve", "approve_with_notes"):
        return ModificationOutcome(
            contract_id=contract.contract_id,
            policy_decision_id=policy_decision.decision_id,
            outcome="applied",
            explanation=(
                f"Change approved and would be applied. Policy action: {action}. "
                "(Phase 1: actual file write not performed.)"
            ),
        )

    return ModificationOutcome(
        contract_id=contract.contract_id,
        policy_decision_id=policy_decision.decision_id,
        outcome="rejected",
        explanation=f"Unknown policy action '{action}'. Change rejected.",
    )
