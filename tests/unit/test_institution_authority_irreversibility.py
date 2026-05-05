"""Phase 4 institution — reviewer authority, reversibility, and halt distinction (Issue #31).

These tests encode **deterministic expectations** for a future `InstitutionBridge` (#30).
Policy helpers live in this module only (regression fixtures, not production authority).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from openayane_rde.core.models import (
    EvidenceBasis,
    ExecutionActionType,
    ExternalSideEffectKind,
    RiskLevel,
)
from openayane_rde.institution import (
    AuthorityRef,
    EvidenceHandoff,
    HaltProvenance,
    InstitutionRule,
    ReviewerAuthority,
)
from openayane_rde.institution.models import InstitutionalDecisionKind

# Same ordering as RDE / policy layers use informally; kept local to tests.
_RISK_ORDER: dict[RiskLevel, int] = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}


def _dt() -> datetime:
    return datetime(2026, 5, 5, 12, 0, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class ActionIntent:
    """Test-only action intent (reversibility: True=irreversible, False=reversible, None=unknown)."""

    action_type: ExecutionActionType
    side_effect: ExternalSideEffectKind
    risk: RiskLevel
    reversibility: bool | None


def reviewer_covers_intent(ra: ReviewerAuthority, intent: ActionIntent) -> bool:
    """Whether the reviewer's *declared* bounds cover the action (test stub)."""

    if intent.action_type not in ra.allowed_action_types:
        return False
    if intent.side_effect not in ra.allowed_side_effects:
        return False
    return _RISK_ORDER[ra.max_risk_level] >= _RISK_ORDER[intent.risk]


def stub_decision(
    ra: ReviewerAuthority,
    rule: InstitutionRule,
    intent: ActionIntent,
) -> InstitutionalDecisionKind:
    """Minimal conservative path for regression tests; mirrors docs/40 §6 spirit."""

    if intent.reversibility is None:
        return "require_more_evidence"
    if not reviewer_covers_intent(ra, intent):
        return "require_higher_authority"
    if intent.reversibility is True:
        if not rule.allows_irreversible_action:
            return "halt_institutionally"
        if not ra.can_approve_irreversible:
            return "require_higher_authority"
    return "accept"


def _base_rule(*, allows_irreversible: bool) -> InstitutionRule:
    return InstitutionRule(
        rule_id="rule_x",
        name="test",
        description="test",
        scope=["*"],
        applies_to_action_types=["network"],
        applies_to_side_effects=["publishing"],
        minimum_authority_level="L1",
        evidence_required=[],
        created_at=_dt(),
        allows_irreversible_action=allows_irreversible,
    )


def _ref() -> AuthorityRef:
    return AuthorityRef(
        authority_id="a1",
        authority_type="human_reviewer",
        subject_id="u1",
        authority_level="L1",
    )


def _reviewer(
    *,
    max_risk: RiskLevel,
    can_irrev: bool,
    actions: list[ExecutionActionType] | None = None,
    effects: list[ExternalSideEffectKind] | None = None,
) -> ReviewerAuthority:
    return ReviewerAuthority(
        reviewer_id="r1",
        authority_refs=[_ref()],
        allowed_action_types=actions or ["network"],
        allowed_side_effects=effects or ["publishing"],
        max_risk_level=max_risk,
        can_approve_irreversible=can_irrev,
    )


def test_reviewer_insufficient_risk_cannot_cover_critical() -> None:
    ra = _reviewer(max_risk="medium", can_irrev=False)
    rule = _base_rule(allows_irreversible=False)
    intent = ActionIntent("network", "publishing", "critical", False)
    assert not reviewer_covers_intent(ra, intent)
    assert stub_decision(ra, rule, intent) == "require_higher_authority"


def test_reviewer_insufficient_action_type() -> None:
    ra = _reviewer(
        max_risk="high",
        can_irrev=False,
        actions=["read"],
        effects=["read_only_fetch"],
    )
    rule = InstitutionRule(
        rule_id="rule_y",
        name="test",
        description="test",
        scope=["*"],
        applies_to_action_types=["execute"],
        applies_to_side_effects=["notification"],
        minimum_authority_level="L1",
        evidence_required=[],
        created_at=_dt(),
    )
    intent = ActionIntent("execute", "notification", "high", False)
    assert not reviewer_covers_intent(ra, intent)
    assert stub_decision(ra, rule, intent) == "require_higher_authority"


def test_reviewer_sufficient_for_allowed_high_risk() -> None:
    ra = _reviewer(max_risk="high", can_irrev=False)
    rule = _base_rule(allows_irreversible=False)
    intent = ActionIntent("network", "publishing", "high", False)
    assert reviewer_covers_intent(ra, intent)
    assert stub_decision(ra, rule, intent) == "accept"


def test_irreversible_requires_elevation_when_reviewer_cannot_approve() -> None:
    ra = _reviewer(max_risk="high", can_irrev=False)
    rule = _base_rule(allows_irreversible=True)
    intent = ActionIntent("network", "publishing", "high", True)
    assert reviewer_covers_intent(ra, intent)
    assert stub_decision(ra, rule, intent) == "require_higher_authority"


def test_irreversible_halts_when_rule_forbids() -> None:
    ra = _reviewer(max_risk="critical", can_irrev=True)
    rule = _base_rule(allows_irreversible=False)
    intent = ActionIntent("network", "publishing", "high", True)
    assert stub_decision(ra, rule, intent) == "halt_institutionally"


def test_unknown_reversibility_requires_more_evidence() -> None:
    ra = _reviewer(max_risk="critical", can_irrev=True)
    rule = _base_rule(allows_irreversible=True)
    intent = ActionIntent("network", "publishing", "low", None)
    assert stub_decision(ra, rule, intent) == "require_more_evidence"


def test_policy_halt_json_differs_from_rde_halt() -> None:
    policy = HaltProvenance(
        halt_kind="policy_halt",
        policy_rule_id="p1",
        explanation="blocked by policy",
    )
    rde = HaltProvenance(
        halt_kind="rde_halt",
        rde_result_id="rde_1",
        explanation="rde structural halt",
    )
    assert policy.model_dump_json() != rde.model_dump_json()
    assert "policy_halt" in policy.model_dump_json()
    assert "rde_halt" in rde.model_dump_json()


def test_evidence_handoff_preserves_audit_ids_and_basis_multiple_shapes() -> None:
    for audit_ids in ([], ["only"], ["a", "b", "c"]):
        basis: list[EvidenceBasis] = (
            ["structural_diff", "human_review_decision"] if audit_ids else ["tool_risk_rule"]
        )
        h = EvidenceHandoff(
            handoff_id="h1",
            contract_id="tc",
            tool_call_id="tcl",
            audit_event_ids=list(audit_ids),
            evidence_basis=basis,
            explanation="x",
            created_at=_dt(),
        )
        h2 = EvidenceHandoff.model_validate_json(h.model_dump_json())
        assert h2.audit_event_ids == audit_ids
        assert h2.evidence_basis == basis


@pytest.mark.parametrize(
    ("policy_kind", "rde_kind"),
    [
        ("policy_halt", "rde_halt"),
        ("runtime_block", "review_rejection"),
    ],
)
def test_distinct_halt_kinds_remain_distinct(policy_kind: str, rde_kind: str) -> None:
    p = HaltProvenance(halt_kind=policy_kind, explanation="p")  # type: ignore[arg-type]
    r = HaltProvenance(halt_kind=rde_kind, explanation="r")  # type: ignore[arg-type]
    assert p.halt_kind != r.halt_kind
