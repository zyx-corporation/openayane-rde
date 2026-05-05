"""Decision provenance — keeps RDE classification distinct from institution overlays."""

from __future__ import annotations

from dataclasses import dataclass

from openayane_rde.core.models import PolicyActionKind, PolicyDecision, RDEResult


@dataclass(frozen=True, slots=True)
class DecisionProvenance:
    """Structured split between RDE output and optional institution metadata."""

    rde_result_id: str
    rde_classification: str
    policy_action: PolicyActionKind
    institution_rule_id: str | None
    institutional_rationale: str | None
    pop_verification_attempted: bool
    pop_verification_passed: bool | None


def provenance_from_policy_decision(
    decision: PolicyDecision,
    rde_result: RDEResult,
    *,
    pop_verification_attempted: bool = False,
    pop_verification_passed: bool | None = None,
) -> DecisionProvenance:
    """Derive provenance for audit exports without conflating RDE with institution text."""

    return DecisionProvenance(
        rde_result_id=decision.rde_result_id,
        rde_classification=rde_result.classification,
        policy_action=decision.action,
        institution_rule_id=decision.institution_rule_id,
        institutional_rationale=decision.institutional_rationale,
        pop_verification_attempted=pop_verification_attempted,
        pop_verification_passed=pop_verification_passed,
    )
