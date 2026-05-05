"""Phase 1 runtime evaluation flow.

Implements the minimal flow described in phase1_implementation_plan.md Section 5:

    structural_diff = run_structural_diff(original, generated_output, task_contract)
    semantic_delta = semantic_delta_stub(structural_diff)
    rde_result = evaluate_rde(task_contract, structural_diff, semantic_delta, generated_output)
    policy_decision = decide_policy(rde_result, task_contract, relation_context)
    audit_event = write_audit_event(...)  # optional, when logging
    return Phase1EvaluationResult(...)
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from openayane_rde.audit.hash import sha256_text
from openayane_rde.audit.log import append_event
from openayane_rde.core.models import (
    AuditEvent,
    EvidenceBasis,
    ExecutionActionType,
    ExternalSideEffectKind,
    GeneratorOutput,
    PolicyDecision,
    PostExecutionDiff,
    RDEResult,
    RelationContext,
    SemanticDelta,
    StructuralDiff,
    TaskContract,
)
from openayane_rde.diff.json_diff import JsonDiff
from openayane_rde.diff.markdown_diff import MarkdownDiff
from openayane_rde.diff.python_ast_diff import PythonAstDiff
from openayane_rde.institution.pop_uid import PopUidAdapter
from openayane_rde.institution.rule_registry import InstitutionRuleRegistry
from openayane_rde.policy.bridge import decide_policy
from openayane_rde.policy.institution_bridge import decide_policy_with_institution
from openayane_rde.rde.core import evaluate_rde
from openayane_rde.runtime.result import Phase1EvaluationResult
from openayane_rde.semantic.delta_engine import estimate_semantic_delta

Domain = Literal["markdown", "json", "python"]

_DIFF_ENGINES = {
    "markdown": MarkdownDiff(),
    "python": PythonAstDiff(),
}


def _policy_decision_with_optional_institution(
    rde_result: RDEResult,
    task_contract: TaskContract,
    relation_context: RelationContext | None,
    *,
    institution_registry: InstitutionRuleRegistry | None,
    institution_action_type: ExecutionActionType | None,
    institution_side_effect: ExternalSideEffectKind | None,
    pop_verifier: PopUidAdapter | None,
    pop_subject_id: str | None,
) -> PolicyDecision:
    if (
        institution_registry is not None
        and institution_action_type is not None
        and institution_side_effect is not None
    ):
        return decide_policy_with_institution(
            rde_result,
            task_contract,
            relation_context,
            institution_registry,
            action_type=institution_action_type,
            side_effect=institution_side_effect,
            pop_verifier=pop_verifier,
            pop_subject_id=pop_subject_id,
        )
    return decide_policy(rde_result, task_contract, relation_context)


def run_structural_diff(
    original: str,
    generator_output: GeneratorOutput,
    contract: TaskContract,
    domain: Domain,
    required_json_fields: list[str] | None = None,
) -> StructuralDiff:
    """Run the appropriate structural diff engine for the given domain."""
    generated = _extract_payload_text(generator_output)

    if domain == "json":
        return JsonDiff(required_fields=required_json_fields or []).diff(
            original, generated, contract, generator_output
        )
    if domain in _DIFF_ENGINES:
        return _DIFF_ENGINES[domain].diff(
            original, generated, contract, generator_output
        )
    raise ValueError(f"Unsupported domain: {domain!r}")


def _extract_payload_text(generator_output: GeneratorOutput) -> str:
    payload = generator_output.payload
    if isinstance(payload, str):
        return payload
    import json

    return json.dumps(payload)


def run_phase1_evaluation(
    original: str,
    generator_output: GeneratorOutput,
    task_contract: TaskContract,
    domain: Domain = "markdown",
    required_json_fields: list[str] | None = None,
    relation_context: RelationContext | None = None,
    audit_log_path: str | Path | None = None,
    *,
    institution_registry: InstitutionRuleRegistry | None = None,
    institution_action_type: ExecutionActionType | None = None,
    institution_side_effect: ExternalSideEffectKind | None = None,
    pop_verifier: PopUidAdapter | None = None,
    pop_subject_id: str | None = None,
) -> Phase1EvaluationResult:
    """Execute the Phase 1 evaluation flow.

    Steps:
      1. Run structural diff
      2. Estimate semantic delta (stub)
      3. Evaluate RDE
      4. Decide policy
      5. Write audit event (optional, when `audit_log_path` is set)

    Optional keyword-only institution hooks (all three registry axes required to
    enable :func:`~openayane_rde.policy.institution_bridge.decide_policy_with_institution`):

    ``institution_registry``, ``institution_action_type``, ``institution_side_effect``,
    plus optional ``pop_verifier`` / ``pop_subject_id``.

    Returns:
        Phase1EvaluationResult with structural diff, semantic delta, RDE result,
        policy decision, and optional audit event (if logged).
    """
    structural_diff = run_structural_diff(
        original,
        generator_output,
        task_contract,
        domain,
        required_json_fields,
    )

    semantic_delta = estimate_semantic_delta(structural_diff, task_contract)

    rde_result = evaluate_rde(
        contract=task_contract,
        generator_output=generator_output,
        structural_diff=structural_diff,
        semantic_delta=semantic_delta,
        relation_context=relation_context,
    )
    _post_evidence: list[EvidenceBasis] = ["structural_diff", "semantic_delta"]
    rde_result = rde_result.model_copy(
        update={
            "evaluation_kind": "post_structural",
            "evidence_basis": _post_evidence,
        }
    )

    policy_decision = _policy_decision_with_optional_institution(
        rde_result,
        task_contract,
        relation_context,
        institution_registry=institution_registry,
        institution_action_type=institution_action_type,
        institution_side_effect=institution_side_effect,
        pop_verifier=pop_verifier,
        pop_subject_id=pop_subject_id,
    )

    audit_event: AuditEvent | None = None
    if audit_log_path is not None:
        audit_event = _write_audit_event(
            task_contract=task_contract,
            generator_output=generator_output,
            structural_diff=structural_diff,
            semantic_delta=semantic_delta,
            rde_result=rde_result,
            policy_decision=policy_decision,
            original=original,
            generated=_extract_payload_text(generator_output),
            audit_log_path=audit_log_path,
        )

    return Phase1EvaluationResult(
        task_contract=task_contract,
        generator_output=generator_output,
        relation_context=relation_context,
        structural_diff=structural_diff,
        semantic_delta=semantic_delta,
        rde_result=rde_result,
        policy_decision=policy_decision,
        audit_event=audit_event,
    )


def _write_audit_event(
    task_contract: TaskContract,
    generator_output: GeneratorOutput,
    structural_diff: StructuralDiff,
    semantic_delta: SemanticDelta,
    rde_result: RDEResult,
    policy_decision: PolicyDecision,
    original: str,
    generated: str,
    audit_log_path: str | Path,
) -> AuditEvent:
    event = AuditEvent(
        actor="rde",
        task_contract_id=task_contract.contract_id,
        generator_output_id=generator_output.output_id,
        structural_diff_id=structural_diff.diff_id,
        semantic_delta_id=semantic_delta.delta_id,
        rde_result_id=rde_result.result_id,
        policy_decision_id=policy_decision.decision_id,
        action="evaluate_rde",
        hash_before=sha256_text(original),
        hash_after=sha256_text(generated),
        explanation=rde_result.explanation,
        payload={
            "classification": rde_result.classification,
            "risk_level": rde_result.risk_level,
            "policy_action": policy_decision.action,
            "evaluation_kind": rde_result.evaluation_kind,
            "evidence_basis": rde_result.evidence_basis,
            "institution_rule_id": policy_decision.institution_rule_id,
            "institutional_rationale": policy_decision.institutional_rationale,
        },
    )
    append_event(audit_log_path, event)
    return event


def run_phase1_evaluation_from_post_execution_diff(
    post_diff: PostExecutionDiff,
    original: str,
    generator_output: GeneratorOutput,
    task_contract: TaskContract,
    domain: Domain = "markdown",
    required_json_fields: list[str] | None = None,
    relation_context: RelationContext | None = None,
    audit_log_path: str | Path | None = None,
    *,
    institution_registry: InstitutionRuleRegistry | None = None,
    institution_action_type: ExecutionActionType | None = None,
    institution_side_effect: ExternalSideEffectKind | None = None,
    pop_verifier: PopUidAdapter | None = None,
    pop_subject_id: str | None = None,
) -> Phase1EvaluationResult:
    """Run Phase 1 RDE on a post-execution diff (structural diff optional).

    If ``post_diff.structural_diff`` / ``semantic_delta`` are set, they are
    reused; otherwise diffing and semantic estimation follow the normal Phase 1
    path. ``rde_result.evaluation_kind`` is ``post_structural``.
    """

    structural_diff = post_diff.structural_diff
    if structural_diff is None:
        structural_diff = run_structural_diff(
            original,
            generator_output,
            task_contract,
            domain,
            required_json_fields,
        )

    semantic_delta = post_diff.semantic_delta
    if semantic_delta is None:
        semantic_delta = estimate_semantic_delta(structural_diff, task_contract)

    rde_result = evaluate_rde(
        contract=task_contract,
        generator_output=generator_output,
        structural_diff=structural_diff,
        semantic_delta=semantic_delta,
        relation_context=relation_context,
    )
    _post_evidence: list[EvidenceBasis] = ["structural_diff", "semantic_delta"]
    if post_diff.unexpected_side_effects or post_diff.protected_resource_changes:
        _post_evidence = _post_evidence + ["observed_side_effects"]
    rde_result = rde_result.model_copy(
        update={"evaluation_kind": "post_structural", "evidence_basis": _post_evidence}
    )

    policy_decision = _policy_decision_with_optional_institution(
        rde_result,
        task_contract,
        relation_context,
        institution_registry=institution_registry,
        institution_action_type=institution_action_type,
        institution_side_effect=institution_side_effect,
        pop_verifier=pop_verifier,
        pop_subject_id=pop_subject_id,
    )

    audit_event: AuditEvent | None = None
    if audit_log_path is not None:
        audit_event = _write_audit_event(
            task_contract=task_contract,
            generator_output=generator_output,
            structural_diff=structural_diff,
            semantic_delta=semantic_delta,
            rde_result=rde_result,
            policy_decision=policy_decision,
            original=original,
            generated=_extract_payload_text(generator_output),
            audit_log_path=audit_log_path,
        )

    return Phase1EvaluationResult(
        task_contract=task_contract,
        generator_output=generator_output,
        relation_context=relation_context,
        structural_diff=structural_diff,
        semantic_delta=semantic_delta,
        rde_result=rde_result,
        policy_decision=policy_decision,
        audit_event=audit_event,
    )
