"""RelationStore update rules from Phase1EvaluationResult (Phase 2)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from openayane_rde.core.ids import new_id
from openayane_rde.core.models import (
    AuditEvent,
    DocumentFragilityProfile,
    DriftPattern,
    DriftPatternKind,
    GeneratorReliabilityProfile,
    RelationContext,
    RelationStoreRecord,
    RelationUpdateSummary,
    RDEResult,
    SemanticDelta,
    StructuralDiff,
)
from openayane_rde.core.time import now_utc
from openayane_rde.runtime.result import Phase1EvaluationResult

if TYPE_CHECKING:
    from openayane_rde.relation.store import RelationStore


def clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def update_relation_context(
    context: RelationContext,
    rde_result: RDEResult,
    audit_event: AuditEvent,
) -> RelationContext:
    """Legacy hook: identity unless callers rely on in-memory mutation."""

    return context


def _generator_id_from_output(result: Phase1EvaluationResult) -> str:
    mi = result.generator_output.model_info
    return f"{mi.provider}:{mi.model}"


def _document_id(result: Phase1EvaluationResult, object_id: str) -> str:
    meta = result.task_contract.metadata
    if isinstance(meta, dict) and meta.get("document_id"):
        return str(meta["document_id"])
    return object_id


def _infer_pattern_kind(
    structural_diff: StructuralDiff,
    rde_result: RDEResult,
) -> DriftPatternKind:
    if structural_diff.self_report_mismatches:
        return "self_report_mismatch"
    if any(pc.element == "citations" for pc in structural_diff.protected_element_changes):
        return "citation_deletion"
    if any(pc.element == "numbers" for pc in structural_diff.protected_element_changes):
        return "number_change"
    if any(pc.element == "definitions" for pc in structural_diff.protected_element_changes):
        return "definition_shift"
    if structural_diff.schema_violations:
        return "required_field_deletion"
    if structural_diff.signature_changes:
        return "signature_change"
    if rde_result.classification == "critical_corruption":
        return "constraint_omission"
    return "other"


def _merge_pattern(
    record: RelationStoreRecord,
    kind: DriftPatternKind,
    example: str,
) -> None:
    for p in record.drift_patterns:
        if p.kind == kind:
            p.count += 1
            if example and len(p.examples) < 5:
                p.examples.append(example)
            p.last_seen_at = now_utc()
            return
    record.drift_patterns.append(
        DriftPattern(kind=kind, examples=[example] if example else [])
    )


def _recompute_generator_profile(p: GeneratorReliabilityProfile) -> None:
    p.reliability_score = clip01(
        1.0
        - 0.15 * p.critical_corruption_count
        - 0.08 * p.self_report_mismatch_count
        - 0.05 * p.suspicious_drift_count
        + 0.01 * p.preserved_count
    )


def _recompute_document_fragility(p: DocumentFragilityProfile) -> None:
    p.fragility_score = clip01(
        0.10 * p.protected_change_count
        + 0.15 * p.citation_break_count
        + 0.12 * p.number_change_count
        + 0.10 * p.definition_shift_count
    )


def _apply_structural_fragility(
    profile: DocumentFragilityProfile,
    structural_diff: StructuralDiff,
) -> None:
    profile.total_edits += 1
    profile.protected_change_count += len(structural_diff.protected_element_changes)
    profile.citation_break_count += len(structural_diff.reference_breaks)
    num_changes = sum(
        1
        for n in structural_diff.changed_nodes + structural_diff.deleted_nodes
        if n.kind == "number"
    )
    profile.number_change_count += num_changes
    def_changes = sum(
        1
        for n in structural_diff.changed_nodes + structural_diff.deleted_nodes
        if n.kind == "definition"
    )
    profile.definition_shift_count += def_changes
    _recompute_document_fragility(profile)


def _apply_classification_metrics(
    record: RelationStoreRecord,
    rde_result: RDEResult,
    structural_diff: StructuralDiff,
    semantic_delta: SemanticDelta,
) -> list[str]:
    patterns_touched: list[str] = []
    cls = rde_result.classification

    if cls == "preserved":
        record.trust = clip01(record.trust + 0.01)
        record.stability = clip01(record.stability + 0.01)
    elif cls == "authorized_deviation":
        record.trust = clip01(record.trust + 0.005)
        record.stability = clip01(record.stability + 0.005)
    elif cls == "benign_incidental_drift":
        record.trust = clip01(record.trust + 0.002)
    elif cls == "creative_deviation":
        record.trust = clip01(record.trust + 0.003)
    elif cls == "suspicious_drift":
        record.trust = clip01(record.trust - 0.03)
        record.stability = clip01(record.stability - 0.02)
        record.suspicious_drift_count += 1
        record.review_threshold_adjustment = clip01(
            record.review_threshold_adjustment + 0.05
        )
    elif cls == "critical_corruption":
        record.trust = clip01(record.trust - 0.10)
        record.stability = clip01(record.stability - 0.05)
        record.critical_corruption_count += 1
        record.review_threshold_adjustment = clip01(
            record.review_threshold_adjustment + 0.15
        )

    if structural_diff.self_report_mismatches:
        record.trust = clip01(record.trust - 0.05)
        record.self_report_mismatch_count += 1
        _merge_pattern(record, "self_report_mismatch", "self-report mismatch")
        patterns_touched.append("self_report_mismatch")

    kind = _infer_pattern_kind(structural_diff, rde_result)
    example = rde_result.explanation[:200] if rde_result.explanation else ""
    _merge_pattern(record, kind, example)
    patterns_touched.append(kind)

    record.last_delta_m = semantic_delta.delta_m_score
    record.interaction_count += 1
    record.updated_at = now_utc()
    return sorted(set(patterns_touched))


def _apply_generator_profile(
    record: RelationStoreRecord,
    rde_result: RDEResult,
    generator_id: str,
) -> None:
    if record.generator_reliability_profile is None:
        record.generator_reliability_profile = GeneratorReliabilityProfile(
            generator_id=generator_id
        )
    p = record.generator_reliability_profile
    p.total_outputs += 1
    cls = rde_result.classification
    if cls == "preserved":
        p.preserved_count += 1
    elif cls == "authorized_deviation":
        p.authorized_deviation_count += 1
    elif cls == "suspicious_drift":
        p.suspicious_drift_count += 1
    elif cls == "critical_corruption":
        p.critical_corruption_count += 1
    if rde_result.classification in ("suspicious_drift", "critical_corruption"):
        pass
    p.self_report_mismatch_count = record.self_report_mismatch_count
    _recompute_generator_profile(p)


def update_relation_from_evaluation_result(
    result: Phase1EvaluationResult,
    store: RelationStore | None = None,
) -> RelationUpdateSummary:
    """Persist relation state when a store and auditable evidence exist."""

    base_rc = result.relation_context or RelationContext()
    subject_id = base_rc.subject_id
    object_id = base_rc.object_id

    if store is None:
        if result.audit_event is None:
            return RelationUpdateSummary(
                context=base_rc,
                updated=False,
                message="No audit event; relation context not correlated via audit pipeline.",
            )
        new_ctx = update_relation_context(base_rc, result.rde_result, result.audit_event)
        return RelationUpdateSummary(
            context=new_ctx,
            updated=False,
            message="No RelationStore provided; in-memory hook only.",
        )

    if result.audit_event is None:
        ctx = store.load_context(subject_id, object_id)
        return RelationUpdateSummary(
            context=ctx,
            updated=False,
            message="Phase 2 Option A: RelationStore update requires an audit_event.",
        )

    existing = store.get(subject_id, object_id)
    trust_before = existing.trust if existing else base_rc.trust
    stability_before = existing.stability if existing else base_rc.stability
    thr_before = (
        existing.review_threshold_adjustment if existing else base_rc.review_threshold_adjustment
    )

    gid = _generator_id_from_output(result)
    doc_id = _document_id(result, object_id)

    if existing is None:
        record = RelationStoreRecord(
            relation_id=new_id("rel"),
            subject_id=subject_id,
            object_id=object_id,
            trust=base_rc.trust,
            stability=base_rc.stability,
            context_affinity=base_rc.context_affinity,
            interaction_count=base_rc.interaction_count,
            generator_reliability_profile=GeneratorReliabilityProfile(generator_id=gid),
            document_fragility_profile=DocumentFragilityProfile(document_id=doc_id),
            review_threshold_adjustment=base_rc.review_threshold_adjustment,
        )
    else:
        record = existing

    if record.generator_reliability_profile is None:
        record.generator_reliability_profile = GeneratorReliabilityProfile(generator_id=gid)
    if record.document_fragility_profile is None:
        record.document_fragility_profile = DocumentFragilityProfile(document_id=doc_id)

    pat = _apply_classification_metrics(
        record, result.rde_result, result.structural_diff, result.semantic_delta
    )
    _apply_generator_profile(record, result.rde_result, gid)
    _apply_structural_fragility(record.document_fragility_profile, result.structural_diff)

    record.last_audit_event_id = result.audit_event.event_id
    store.upsert(record)

    ctx = store.load_context(subject_id, object_id)
    return RelationUpdateSummary(
        context=ctx,
        updated=True,
        relation_id=record.relation_id,
        trust_before=trust_before,
        trust_after=record.trust,
        stability_before=stability_before,
        stability_after=record.stability,
        review_threshold_adjustment_before=thr_before,
        review_threshold_adjustment_after=record.review_threshold_adjustment,
        updated_patterns=pat,
        message="RelationStore updated from audited Phase1EvaluationResult.",
    )
