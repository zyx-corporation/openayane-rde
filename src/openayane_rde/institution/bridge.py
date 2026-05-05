"""Deterministic Institution Bridge — EvidenceHandoff to InstitutionalDecision (Phase 4 MVP).

Rule-based and inspectable; no LLM calls. See ``docs/40_openayane_rde_phase4_institution_bridge_spec.md``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from openayane_rde.core.ids import new_id
from openayane_rde.core.models import (
    EvidenceBasis,
    ExecutionActionType,
    ExecutionGateEvaluation,
    ExternalSideEffectKind,
    RiskLevel,
    ToolExecutionResult,
)
from openayane_rde.core.time import now_utc
from openayane_rde.institution.models import (
    EvidenceHandoff,
    InstitutionalDecision,
    InstitutionalDecisionKind,
    InstitutionRule,
    ReviewerAuthority,
)
from openayane_rde.institution.policy import first_matching_rule, reviewer_covers_action


@dataclass(frozen=True, slots=True)
class HandoffDecisionInput:
    """Phase 3–derived facts for rule matching (not stored on ``EvidenceHandoff``)."""

    action_type: ExecutionActionType
    side_effect: ExternalSideEffectKind
    risk_level: RiskLevel
    """True = irreversible, False = reversible, None = unknown (conservative)."""
    reversibility: bool | None = None


class DeterministicInstitutionBridge:
    """Match ``InstitutionRule`` and ``ReviewerAuthority`` to produce ``InstitutionalDecision``."""

    def build_handoff(
        self,
        *,
        handoff_id: str,
        evaluation: ExecutionGateEvaluation,
        execution_result: ToolExecutionResult | None = None,
        review_request_id: str | None = None,
        review_decision_id: str | None = None,
        rde_result_id: str | None = None,
        extra_audit_event_ids: list[str] | None = None,
        explanation: str,
        created_at: datetime | None = None,
    ) -> EvidenceHandoff:
        ge = evaluation.decision
        contract = evaluation.contract
        audit_ids: list[str] = []
        if ge.audit_event_id:
            audit_ids.append(ge.audit_event_id)
        if execution_result and execution_result.audit_event_id:
            audit_ids.append(execution_result.audit_event_id)
        if extra_audit_event_ids:
            audit_ids.extend(extra_audit_event_ids)

        evidence_basis: list[EvidenceBasis] = []
        if ge.rde_result and ge.rde_result.evidence_basis:
            evidence_basis = list(ge.rde_result.evidence_basis)

        resolved_rde_id = rde_result_id
        if resolved_rde_id is None and ge.rde_result is not None:
            resolved_rde_id = ge.rde_result.result_id

        return EvidenceHandoff(
            handoff_id=handoff_id,
            contract_id=contract.contract_id,
            tool_call_id=contract.source_tool_call_id,
            gate_decision_id=ge.decision_id,
            review_request_id=review_request_id,
            review_decision_id=review_decision_id,
            execution_id=execution_result.execution_id if execution_result else None,
            rde_result_id=resolved_rde_id,
            audit_event_ids=audit_ids,
            evidence_basis=evidence_basis,
            explanation=explanation,
            created_at=created_at or now_utc(),
        )

    def decide(
        self,
        handoff: EvidenceHandoff,
        rules: list[InstitutionRule],
        reviewer_authority: ReviewerAuthority | None = None,
        *,
        decision_input: HandoffDecisionInput,
    ) -> InstitutionalDecision:
        inp = decision_input

        if not handoff.audit_event_ids and not handoff.evidence_basis:
            return self._decision(
                handoff,
                decision="require_more_evidence",
                rule_id=None,
                authority_id=None,
                rationale="Handoff has neither audit_event_ids nor evidence_basis.",
            )

        if inp.reversibility is None:
            return self._decision(
                handoff,
                decision="require_more_evidence",
                rule_id=None,
                authority_id=None,
                rationale="Reversibility unknown; cannot accept institutionally.",
            )

        rule = first_matching_rule(
            rules,
            action_type=inp.action_type,
            side_effect=inp.side_effect,
        )
        if rule is None:
            return self._decision(
                handoff,
                decision="require_more_evidence",
                rule_id=None,
                authority_id=None,
                rationale="No InstitutionRule matched the declared action and side effect.",
            )

        if handoff.review_decision_id is not None and reviewer_authority is None:
            return self._decision(
                handoff,
                decision="require_higher_authority",
                rule_id=rule.rule_id,
                authority_id=None,
                rationale="Human review decision referenced but no ReviewerAuthority provided.",
            )

        if inp.reversibility is True:
            if not rule.allows_irreversible_action:
                return self._decision(
                    handoff,
                    decision="halt_institutionally",
                    rule_id=rule.rule_id,
                    authority_id=self._primary_authority_id(reviewer_authority),
                    rationale="Matched rule does not allow irreversible acceptance.",
                    risk_accepted=False,
                    irreversible_accepted=False,
                )
            if reviewer_authority is None:
                return self._decision(
                    handoff,
                    decision="require_higher_authority",
                    rule_id=rule.rule_id,
                    authority_id=None,
                    rationale="Irreversible consequence requires ReviewerAuthority.",
                )
            if not reviewer_authority.can_approve_irreversible:
                return self._decision(
                    handoff,
                    decision="require_higher_authority",
                    rule_id=rule.rule_id,
                    authority_id=self._primary_authority_id(reviewer_authority),
                    rationale="Reviewer cannot approve irreversible actions.",
                )

        if reviewer_authority is not None:
            if not reviewer_covers_action(
                reviewer_authority,
                action_type=inp.action_type,
                side_effect=inp.side_effect,
                action_risk=inp.risk_level,
            ):
                return self._decision(
                    handoff,
                    decision="require_higher_authority",
                    rule_id=rule.rule_id,
                    authority_id=self._primary_authority_id(reviewer_authority),
                    rationale="ReviewerAuthority does not cover this action or risk.",
                )

        return self._decision(
            handoff,
            decision="accept",
            rule_id=rule.rule_id,
            authority_id=self._primary_authority_id(reviewer_authority),
            rationale="Matched rule and authority bounds accept this consequence.",
            risk_accepted=True,
            irreversible_accepted=bool(inp.reversibility),
        )

    def _primary_authority_id(self, ra: ReviewerAuthority | None) -> str | None:
        if ra is None or not ra.authority_refs:
            return None
        return ra.authority_refs[0].authority_id

    def _primary_audit_link(self, handoff: EvidenceHandoff) -> str | None:
        return handoff.audit_event_ids[0] if handoff.audit_event_ids else None

    def _decision(
        self,
        handoff: EvidenceHandoff,
        *,
        decision: InstitutionalDecisionKind,
        rule_id: str | None,
        authority_id: str | None,
        rationale: str,
        risk_accepted: bool = False,
        irreversible_accepted: bool = False,
    ) -> InstitutionalDecision:
        return InstitutionalDecision(
            institutional_decision_id=new_id("instd"),
            handoff_id=handoff.handoff_id,
            rule_id=rule_id,
            authority_id=authority_id,
            decision=decision,
            rationale=rationale,
            risk_accepted=risk_accepted,
            irreversible_accepted=irreversible_accepted,
            audit_event_id=self._primary_audit_link(handoff),
            created_at=now_utc(),
        )
