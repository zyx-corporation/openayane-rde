"""RDE Core: orchestrate RDE evaluation for Phase 1."""

from __future__ import annotations

from openayane_rde.core.models import (
    ConstraintViolation,
    GeneratorOutput,
    RDEResult,
    RelationContext,
    RiskLevel,
    ScoreDetails,
    SemanticDelta,
    StructuralDiff,
    SuspiciousElement,
    TaskContract,
)
from openayane_rde.rde.classifier import classify
from openayane_rde.rde.scoring import (
    score_authorization,
    score_preservation,
    score_resonance,
    score_self_report_mismatch,
    score_structural_risk,
)


def evaluate_rde(
    contract: TaskContract,
    generator_output: GeneratorOutput | None,
    structural_diff: StructuralDiff,
    semantic_delta: SemanticDelta,
    relation_context: RelationContext | None = None,
) -> RDEResult:
    """Evaluate RDE and produce an RDEResult.

    Args:
        contract: The TaskContract for this evaluation.
        generator_output: The GeneratorOutput (used for self-report mismatch context).
        structural_diff: The StructuralDiff from the diff engine.
        semantic_delta: The SemanticDelta (stub in Phase 1).
        relation_context: Optional RelationContext for resonance scoring.

    Returns:
        An RDEResult with classification, scores, and recommended action.
    """
    if relation_context is None:
        from openayane_rde.relation.context_loader import load_neutral_context

        relation_context = load_neutral_context()

    preservation = score_preservation(structural_diff, contract)
    authorization = score_authorization(structural_diff, contract, semantic_delta)
    mismatch = score_self_report_mismatch(structural_diff)
    structural_risk = score_structural_risk(structural_diff, contract)
    resonance = score_resonance(preservation, authorization, relation_context)

    classification, risk_level, required_action = classify(
        preservation_score=preservation,
        authorization_score=authorization,
        structural_risk_score=structural_risk,
        self_report_mismatch_score=mismatch,
        structural_diff=structural_diff,
        contract=contract,
        semantic_delta=semantic_delta,
    )

    violated_constraints = _build_violated_constraints(structural_diff, contract)
    suspicious_elements = _build_suspicious_elements(structural_diff)
    explanation = _build_explanation(
        classification,
        structural_diff,
        contract,
        preservation,
        authorization,
        mismatch,
    )

    return RDEResult(
        contract_id=contract.contract_id,
        classification=classification,
        resonance_score=resonance,
        preservation_score=preservation,
        authorization_score=authorization,
        risk_level=risk_level,
        violated_constraints=violated_constraints,
        suspicious_elements=suspicious_elements,
        required_action=required_action,
        explanation=explanation,
        score_details=ScoreDetails(
            structural_risk_score=structural_risk,
            semantic_delta_score=semantic_delta.delta_m_score,
            self_report_mismatch_score=mismatch,
            relation_adjustment_score=0.0,
        ),
    )


def _build_violated_constraints(
    structural_diff: StructuralDiff,
    contract: TaskContract,
) -> list[ConstraintViolation]:
    violations: list[ConstraintViolation] = []

    for pc in structural_diff.protected_element_changes:
        pc_sev: RiskLevel
        if pc.risk_hint in ("low", "medium", "high", "critical"):
            pc_sev = pc.risk_hint
        else:
            pc_sev = "medium"
        violations.append(
            ConstraintViolation(
                constraint=f"{pc.element} must not be {pc.change_type}",
                path=pc.path,
                description=pc.description,
                severity=pc_sev,
            )
        )

    for sv in structural_diff.schema_violations:
        sv_sev: RiskLevel
        if sv.risk_hint in ("low", "medium", "high", "critical"):
            sv_sev = sv.risk_hint
        else:
            sv_sev = "high"
        violations.append(
            ConstraintViolation(
                constraint=sv.violation_type,
                path=sv.path,
                description=sv.description,
                severity=sv_sev,
            )
        )

    for forbidden in contract.forbidden_delta_m:
        for node in structural_diff.changed_nodes + structural_diff.deleted_nodes:
            if forbidden.lower() in node.description.lower():
                violations.append(
                    ConstraintViolation(
                        constraint=f"forbidden: {forbidden}",
                        path=node.path,
                        description=f"Forbidden change '{forbidden}' detected at {node.path}.",
                        severity="high",
                    )
                )

    return violations


def _build_suspicious_elements(
    structural_diff: StructuralDiff,
) -> list[SuspiciousElement]:
    suspicious: list[SuspiciousElement] = []

    for pc in structural_diff.protected_element_changes:
        suspicious.append(
            SuspiciousElement(
                element=pc.element,
                path=pc.path,
                description=pc.description,
                risk_hint=("high" if pc.risk_hint == "unknown" else pc.risk_hint),
            )
        )

    for mismatch in structural_diff.self_report_mismatches:
        suspicious.append(
            SuspiciousElement(
                element="self_report_mismatch",
                path="/self_report",
                description=mismatch.description,
                risk_hint=(
                    "high" if mismatch.risk_hint == "unknown" else mismatch.risk_hint
                ),
            )
        )

    return suspicious


def _build_explanation(
    classification: str,
    structural_diff: StructuralDiff,
    contract: TaskContract,
    preservation: float,
    authorization: float,
    mismatch: float,
) -> str:
    parts: list[str] = [
        f"Classification: {classification}.",
        f"Preservation score: {preservation:.2f}.",
        f"Authorization score: {authorization:.2f}.",
    ]

    if structural_diff.protected_element_changes:
        elements = ", ".join(
            {pc.element for pc in structural_diff.protected_element_changes}
        )
        parts.append(f"Protected element changes detected: {elements}.")

    if structural_diff.self_report_mismatches:
        parts.append(
            f"Generator self-report mismatch detected "
            f"({len(structural_diff.self_report_mismatches)} mismatch(es))."
        )

    if structural_diff.schema_violations:
        parts.append(
            f"Schema violations: {len(structural_diff.schema_violations)}."
        )

    if classification == "critical_corruption":
        parts.append(
            "Critical corruption: changes to protected elements that may not be applied automatically."
        )
    elif classification == "suspicious_drift":
        parts.append(
            "Suspicious drift: unrequested or undisclosed changes detected. Human review required."
        )
    elif classification == "authorized_deviation":
        parts.append("Changes are within the allowed_delta_m scope.")
    elif classification == "preserved":
        parts.append("No significant structural changes detected. Content appears preserved.")

    return " ".join(parts)
