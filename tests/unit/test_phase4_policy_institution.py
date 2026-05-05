"""Phase 4 completion: institution registry, policy bridge, PoP hook, provenance."""

from __future__ import annotations

from datetime import UTC, datetime

from openayane_rde.contract.builder import build_contract
from openayane_rde.core.models import RDEResult
from openayane_rde.institution import (
    ActorRole,
    DecisionProvenance,
    InstitutionRule,
    InstitutionRuleRegistry,
    Permission,
    provenance_from_policy_decision,
)
from openayane_rde.policy.bridge import decide_policy
from openayane_rde.policy.institution_bridge import decide_policy_with_institution


def _dt() -> datetime:
    return datetime(2026, 5, 5, 12, 0, tzinfo=UTC)


def _rule(
    *,
    rule_id: str = "rule_pub",
    requires_human_review: bool = False,
    requires_rollback_plan: bool = False,
) -> InstitutionRule:
    return InstitutionRule(
        rule_id=rule_id,
        name="publish",
        description="test",
        scope=["*"],
        applies_to_action_types=["network"],
        applies_to_side_effects=["publishing"],
        minimum_authority_level="L1",
        evidence_required=[],
        created_at=_dt(),
        requires_human_review=requires_human_review,
        requires_rollback_plan=requires_rollback_plan,
    )


def _contract_and_rde(
    *,
    classification: str = "preserved",
    risk_level: str = "low",
) -> tuple[object, RDEResult]:
    contract = build_contract(
        mode="preservation",
        requested_action="test",
        protected_elements=["claims"],
    )
    rde = RDEResult(
        contract_id=contract.contract_id,  # type: ignore[union-attr]
        classification=classification,  # type: ignore[arg-type]
        resonance_score=0.9,
        preservation_score=0.9,
        authorization_score=0.9,
        risk_level=risk_level,  # type: ignore[arg-type]
        violated_constraints=[],
        suspicious_elements=[],
        required_action="approve",
        explanation="ok",
    )
    return contract, rde


def test_registry_first_match_order() -> None:
    r1 = _rule(rule_id="first")
    r2 = _rule(rule_id="second")
    reg = InstitutionRuleRegistry([r1, r2])
    assert reg.first_match(action_type="network", side_effect="publishing") is r1


def test_decide_policy_with_institution_no_rule_same_as_base() -> None:
    contract, rde = _contract_and_rde()
    base = decide_policy(rde, contract)  # type: ignore[arg-type]
    reg = InstitutionRuleRegistry([])
    out = decide_policy_with_institution(
        rde,
        contract,  # type: ignore[arg-type]
        None,
        reg,
        action_type="network",
        side_effect="publishing",
    )
    assert out.action == base.action
    assert out.institution_rule_id is None
    assert out.institutional_rationale is None


def test_institution_escalates_to_human_review() -> None:
    contract, rde = _contract_and_rde()
    reg = InstitutionRuleRegistry([_rule(requires_human_review=True)])
    out = decide_policy_with_institution(
        rde,
        contract,  # type: ignore[arg-type]
        None,
        reg,
        action_type="network",
        side_effect="publishing",
    )
    assert out.action == "human_review"
    assert out.institution_rule_id == "rule_pub"
    assert out.institutional_rationale is not None


def test_pop_critical_failed_halts() -> None:
    contract, rde = _contract_and_rde(classification="preserved", risk_level="critical")

    class BadPop:
        def has_valid_pop(self, subject_id: str) -> bool:
            return False

    reg = InstitutionRuleRegistry([])
    out = decide_policy_with_institution(
        rde,
        contract,  # type: ignore[arg-type]
        None,
        reg,
        action_type="network",
        side_effect="publishing",
        pop_verifier=BadPop(),
        pop_subject_id="subj",
    )
    assert out.action == "halt"
    assert out.institutional_rationale is not None


def test_pop_critical_passes_no_pop_halt() -> None:
    contract, rde = _contract_and_rde(classification="preserved", risk_level="critical")

    class GoodPop:
        def has_valid_pop(self, subject_id: str) -> bool:
            return True

    reg = InstitutionRuleRegistry([])
    out = decide_policy_with_institution(
        rde,
        contract,  # type: ignore[arg-type]
        None,
        reg,
        action_type="network",
        side_effect="publishing",
        pop_verifier=GoodPop(),
        pop_subject_id="subj",
    )
    assert out.action == "approve"


def test_permission_and_actor_role_json_round_trip() -> None:
    p = Permission(permission_id="perm_a", description="approve patches")
    role = ActorRole(
        role_id="role_1",
        name="Maintainer",
        permission_ids=[p.permission_id],
    )
    role2 = ActorRole.model_validate_json(role.model_dump_json())
    assert role2.permission_ids == ["perm_a"]


def test_provenance_splits_layers() -> None:
    contract, rde = _contract_and_rde()
    reg = InstitutionRuleRegistry([_rule(requires_human_review=True)])
    decision = decide_policy_with_institution(
        rde,
        contract,  # type: ignore[arg-type]
        None,
        reg,
        action_type="network",
        side_effect="publishing",
    )
    prov: DecisionProvenance = provenance_from_policy_decision(decision, rde)
    assert prov.rde_classification == "preserved"
    assert prov.institution_rule_id == "rule_pub"
    assert prov.policy_action == "human_review"


def test_provenance_records_pop_verification_flags() -> None:
    contract, rde = _contract_and_rde()
    base = decide_policy(rde, contract)  # type: ignore[arg-type]
    prov = provenance_from_policy_decision(
        base,
        rde,
        pop_verification_attempted=True,
        pop_verification_passed=False,
    )
    assert prov.pop_verification_attempted is True
    assert prov.pop_verification_passed is False


def test_rollback_plan_only_adds_institution_note_without_escalating_action() -> None:
    """InstitutionRule.requires_rollback_plan alone must not force human_review."""

    contract, rde = _contract_and_rde()
    reg = InstitutionRuleRegistry(
        [_rule(requires_rollback_plan=True, requires_human_review=False)]
    )
    out = decide_policy_with_institution(
        rde,
        contract,  # type: ignore[arg-type]
        None,
        reg,
        action_type="network",
        side_effect="publishing",
    )
    assert out.action == "approve"
    assert out.institution_rule_id == "rule_pub"
    assert out.institutional_rationale is not None
    assert "rollback" in out.institutional_rationale.lower()


def test_registry_register_preserves_first_match_order() -> None:
    r1 = _rule(rule_id="first")
    r2 = _rule(rule_id="second")
    reg = InstitutionRuleRegistry()
    reg.register(r1)
    reg.register(r2)
    assert reg.first_match(action_type="network", side_effect="publishing") is r1
    assert len(reg.rules) == 2
