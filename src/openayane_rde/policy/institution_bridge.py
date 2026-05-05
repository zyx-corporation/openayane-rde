"""Institution-aware policy adjustment on top of RDE-derived :class:`~openayane_rde.core.models.PolicyDecision`.

RDE classification stays in :class:`~openayane_rde.core.models.RDEResult`; this layer may escalate
policy actions using :class:`~openayane_rde.institution.models.InstitutionRule` without claiming a new semantic evaluation.
"""

from __future__ import annotations

from openayane_rde.core.models import (
    ExecutionActionType,
    ExternalSideEffectKind,
    PolicyDecision,
    RelationContext,
    RDEResult,
    TaskContract,
)
from openayane_rde.institution.pop_uid import PopUidAdapter
from openayane_rde.institution.rule_registry import InstitutionRuleRegistry
from openayane_rde.policy.bridge import decide_policy


def decide_policy_with_institution(
    rde_result: RDEResult,
    contract: TaskContract,
    relation_context: RelationContext | None,
    registry: InstitutionRuleRegistry,
    *,
    action_type: ExecutionActionType,
    side_effect: ExternalSideEffectKind,
    pop_verifier: PopUidAdapter | None = None,
    pop_subject_id: str | None = None,
) -> PolicyDecision:
    """Same inputs as :func:`~openayane_rde.policy.bridge.decide_policy`, plus institution hooks.

    ``action_type`` / ``side_effect`` describe the governed execution (Phase 3 contract axes),
    not the Phase 1 TaskContract surface alone.
    """

    base = decide_policy(rde_result, contract, relation_context)

    if (
        pop_verifier is not None
        and pop_subject_id is not None
        and rde_result.risk_level == "critical"
        and not pop_verifier.has_valid_pop(pop_subject_id)
    ):
        inst = (
            "PoP-UID / institutional identity could not be verified; "
            "critical path halted by institution policy."
        )
        return PolicyDecision(
            contract_id=base.contract_id,
            rde_result_id=base.rde_result_id,
            action="halt",
            rationale=f"{base.rationale} [Institution] {inst}",
            institution_rule_id=None,
            institutional_rationale=inst,
            metadata=dict(base.metadata),
            created_at=base.created_at,
        )

    rule = registry.first_match(
        action_type=action_type,
        side_effect=side_effect,
    )
    if rule is None:
        return base

    action = base.action
    inst_parts: list[str] = []
    if rule.requires_human_review and action in ("approve", "approve_with_notes"):
        action = "human_review"
        inst_parts.append(
            f"InstitutionRule {rule.rule_id} requires human review before apply."
        )
    if rule.requires_rollback_plan:
        inst_parts.append(
            f"InstitutionRule {rule.rule_id} requires a recorded rollback plan."
        )

    inst_text = " ".join(inst_parts) if inst_parts else None
    rationale = base.rationale
    if inst_text:
        rationale = f"{base.rationale} [Institution] {inst_text}"

    return PolicyDecision(
        contract_id=base.contract_id,
        rde_result_id=base.rde_result_id,
        action=action,
        rationale=rationale,
        institution_rule_id=rule.rule_id,
        institutional_rationale=inst_text,
        metadata=dict(base.metadata),
        created_at=base.created_at,
    )
