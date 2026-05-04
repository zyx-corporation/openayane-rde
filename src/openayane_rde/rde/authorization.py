"""allowed_delta_m / forbidden_delta_m matching against structural and semantic signals."""

from __future__ import annotations

from openayane_rde.core.models import (
    AllowedDeltaMatchResult,
    SemanticDelta,
    StructuralDiff,
    TaskContract,
)


def _norm(s: str) -> str:
    return s.lower()


def _collect_signals(
    structural_diff: StructuralDiff,
    semantic_delta: SemanticDelta,
) -> list[tuple[str, str]]:
    """Return (label, text) tuples for keyword matching."""

    out: list[tuple[str, str]] = []
    for nodes, tag in (
        (structural_diff.changed_nodes, "changed"),
        (structural_diff.deleted_nodes, "deleted"),
        (structural_diff.added_nodes, "added"),
    ):
        for n in nodes:
            out.append((tag, f"{n.path} {n.description} kind={n.kind}"))
    for pc in structural_diff.protected_element_changes:
        out.append(
            ("protected", f"{pc.element} {pc.path} {pc.description} {pc.change_type}")
        )
    for sv in structural_diff.schema_violations:
        out.append(("schema", f"{sv.path} {sv.description}"))
    for paths, label in (
        (semantic_delta.changed_definitions, "sem_def"),
        (semantic_delta.changed_numbers, "sem_num"),
        (semantic_delta.changed_references, "sem_ref"),
        (semantic_delta.changed_constraints, "sem_con"),
        (semantic_delta.changed_claims, "sem_claim"),
        (semantic_delta.changed_safety_conditions, "sem_safe"),
    ):
        for p in paths:
            out.append((label, str(p)))
    return out


def match_allowed_delta(
    structural_diff: StructuralDiff,
    semantic_delta: SemanticDelta,
    contract: TaskContract,
) -> AllowedDeltaMatchResult:
    """Match contract phrases against extracted change descriptions (Phase 2 baseline rules)."""

    signals = _collect_signals(structural_diff, semantic_delta)
    allowed_phrases = [_norm(a) for a in contract.allowed_delta_m]
    forbidden_phrases = [_norm(f) for f in contract.forbidden_delta_m]

    matched: list[str] = []
    unmatched: list[str] = []
    forbidden_hits: list[str] = []

    for label, text in signals:
        lower = _norm(text)
        hit_forbidden = [fp for fp in forbidden_phrases if fp and fp in lower]
        if hit_forbidden:
            forbidden_hits.append(f"{label}: {text} (forbidden: {hit_forbidden})")
            continue
        if label == "protected":
            unmatched.append(f"{label}: {text}")
            continue
        hit_allowed = [ap for ap in allowed_phrases if ap and ap in lower]
        if allowed_phrases and hit_allowed:
            matched.append(f"{label}: {text} (matched: {hit_allowed})")
        elif allowed_phrases:
            unmatched.append(f"{label}: {text}")

    total_non_forbidden = len(signals) - len(forbidden_hits)
    if total_non_forbidden <= 0:
        score = 1.0 if not forbidden_hits else 0.0
    elif not allowed_phrases:
        score = 1.0 if not unmatched else 0.5
    else:
        score = len(matched) / max(1, len(matched) + len(unmatched))

    parts = [
        f"matched={len(matched)} unmatched={len(unmatched)} forbidden={len(forbidden_hits)}",
        f"score={score:.2f}",
    ]
    return AllowedDeltaMatchResult(
        matched_changes=matched,
        unmatched_changes=unmatched,
        forbidden_matches=forbidden_hits,
        match_score=score,
        explanation="; ".join(parts),
    )
