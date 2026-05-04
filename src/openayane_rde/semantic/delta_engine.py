"""SemanticDelta Engine: Phase 1 baseline scoring + Phase 2 structural candidate extraction.

Uses :func:`semantic_delta_stub` for conservative scores, then enriches lists from
:class:`StructuralDiff` by domain. LLM evaluation is not used; see ``semantic_mode``.
"""

from __future__ import annotations

from openayane_rde.core.models import SemanticDelta, StructuralDiff, TaskContract
from openayane_rde.semantic.stub import semantic_delta_stub


def estimate_semantic_delta(
    structural_diff: StructuralDiff,
    contract: TaskContract,
) -> SemanticDelta:
    """Estimate semantic delta from structural diff.

    Phase 2: enrich stub output with domain-specific structural cues (no LLM).
    """
    delta = semantic_delta_stub(structural_diff, contract)
    return _phase2_structural_extract(structural_diff, delta)


def _phase2_structural_extract(
    structural_diff: StructuralDiff,
    delta: SemanticDelta,
) -> SemanticDelta:
    domain = structural_diff.domain
    claims: list[str] = []
    constraints: list[str] = []
    definitions = list(delta.changed_definitions)
    numbers = list(delta.changed_numbers)
    references = list(delta.changed_references)
    safety: list[str] = []

    if domain == "markdown":
        for n in structural_diff.deleted_nodes + structural_diff.changed_nodes:
            if n.kind in ("heading", "section"):
                claims.append(n.path)
    elif domain == "json":
        for sv in structural_diff.schema_violations:
            constraints.append(sv.path)
            safety.append(sv.description[:160])
        for pc in structural_diff.protected_element_changes:
            if pc.element in ("required_fields", "schema_keys"):
                constraints.append(pc.path)
    elif domain == "python":
        for n in structural_diff.signature_changes:
            constraints.append(n.path)
        for n in structural_diff.deleted_nodes:
            low = n.path.lower()
            if "test" in low or low.endswith("_test.py"):
                safety.append(n.path)

    delta.changed_claims = claims
    delta.changed_constraints = constraints
    delta.changed_definitions = sorted(set(definitions))
    delta.changed_numbers = sorted(set(numbers))
    delta.changed_references = sorted(set(references))
    delta.changed_safety_conditions = sorted(set(safety))
    delta.is_stub = True
    delta.semantic_mode = "structural_baseline"
    return delta
