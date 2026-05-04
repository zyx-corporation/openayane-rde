"""Phase 1 SemanticDelta stub.

In Phase 1, full semantic evaluation is not implemented.
This stub returns a neutral SemanticDelta derived from structural diff signals.
"""

from __future__ import annotations

from openayane_rde.core.models import SemanticDelta, StructuralDiff, TaskContract


def semantic_delta_stub(
    structural_diff: StructuralDiff,
    contract: TaskContract,
) -> SemanticDelta:
    """Produce a minimal SemanticDelta from structural diff signals.

    Phase 1 does not perform LLM-based semantic evaluation.
    The stub uses structural evidence to estimate a conservative delta_m_score.
    """
    num_protected = len(structural_diff.protected_element_changes)
    num_mismatches = len(structural_diff.self_report_mismatches)
    num_schema_violations = len(structural_diff.schema_violations)

    raw_score = min(
        1.0,
        (num_protected * 0.3)
        + (num_mismatches * 0.2)
        + (num_schema_violations * 0.15),
    )

    changed_definitions = [
        n.path
        for n in structural_diff.changed_nodes
        if n.kind == "definition"
    ]
    changed_numbers = [
        n.path
        for n in structural_diff.changed_nodes + structural_diff.deleted_nodes
        if n.kind == "number"
    ]
    changed_references = [
        n.path
        for n in structural_diff.deleted_nodes
        if n.kind in ("citation", "link")
    ]

    equivalence = max(0.0, 1.0 - raw_score)

    return SemanticDelta(
        contract_id=contract.contract_id,
        delta_m_score=raw_score,
        changed_claims=[],
        changed_constraints=[],
        changed_definitions=changed_definitions,
        changed_numbers=changed_numbers,
        changed_references=changed_references,
        changed_safety_conditions=[],
        semantic_equivalence_score=equivalence,
        uncertainty=0.5,
        is_stub=True,
    )
