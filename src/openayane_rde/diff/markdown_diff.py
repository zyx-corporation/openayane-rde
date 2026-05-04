"""Markdown structural diff engine for OpenAyane RDE Phase 1.

Detected elements:
  - headings
  - paragraphs
  - definitions
  - citations
  - links
  - code blocks
  - numbers
  - dates
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from openayane_rde.core.models import (
    DiffNode,
    GeneratorOutput,
    ProtectedChange,
    SelfReportMismatch,
    StructuralDiff,
    TaskContract,
)
from openayane_rde.diff.base import StructuralDiffEngine

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

_RE_HEADING = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
_RE_CITATION = re.compile(r"\[([^\]]+)\]\(([^)]+)\)|\[(\d+)\]|\\cite\{([^}]+)\}")
_RE_DEFINITION = re.compile(
    r"^(?:\*\*([^*]+)\*\*|__([^_]+)__)[\s]*[:：](.+)$", re.MULTILINE
)
_RE_NUMBER = re.compile(r"\b\d+(?:[.,]\d+)*\b")
_RE_DATE = re.compile(
    r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b"
    r"|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b"
)
_RE_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_RE_CODE_BLOCK = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)


# ---------------------------------------------------------------------------
# Markdown element extractors
# ---------------------------------------------------------------------------


@dataclass
class _MarkdownElements:
    headings: list[tuple[int, str, int]] = field(default_factory=list)
    definitions: list[tuple[str, str, int]] = field(default_factory=list)
    citations: list[tuple[str, int]] = field(default_factory=list)
    links: list[tuple[str, str, int]] = field(default_factory=list)
    code_blocks: list[tuple[str, int]] = field(default_factory=list)
    numbers: list[tuple[str, int]] = field(default_factory=list)
    dates: list[tuple[str, int]] = field(default_factory=list)


def _extract_elements(text: str) -> _MarkdownElements:
    elems = _MarkdownElements()

    for m in _RE_HEADING.finditer(text):
        level = len(m.group(1))
        title = m.group(2).strip()
        elems.headings.append((level, title, m.start()))

    for m in _RE_DEFINITION.finditer(text):
        term = (m.group(1) or m.group(2) or "").strip()
        body = m.group(3).strip()
        elems.definitions.append((term, body, m.start()))

    for m in _RE_CITATION.finditer(text):
        raw = m.group(0)
        elems.citations.append((raw, m.start()))

    for m in _RE_LINK.finditer(text):
        elems.links.append((m.group(1), m.group(2), m.start()))

    for m in _RE_CODE_BLOCK.finditer(text):
        elems.code_blocks.append((m.group(1), m.start()))

    for m in _RE_DATE.finditer(text):
        elems.dates.append((m.group(0), m.start()))

    date_spans = {m.start() for m in _RE_DATE.finditer(text)}
    for m in _RE_NUMBER.finditer(text):
        if m.start() not in date_spans:
            elems.numbers.append((m.group(0), m.start()))

    return elems


def _heading_key(h: tuple[int, str, int]) -> tuple[int, str]:
    return (h[0], h[1])


def _list_to_set(items: list[tuple[str, ...]]) -> set[tuple[str, ...]]:
    return {item[:-1] for item in items}


# ---------------------------------------------------------------------------
# MarkdownDiff
# ---------------------------------------------------------------------------


class MarkdownDiff(StructuralDiffEngine):
    """Structural diff engine for Markdown documents."""

    domain = "markdown"

    def diff(
        self,
        original: str,
        generated: str,
        contract: TaskContract,
        generator_output: GeneratorOutput | None = None,
    ) -> StructuralDiff:
        orig = _extract_elements(original)
        gen = _extract_elements(generated)

        changed_nodes: list[DiffNode] = []
        added_nodes: list[DiffNode] = []
        deleted_nodes: list[DiffNode] = []
        protected_element_changes: list[ProtectedChange] = []
        self_report_mismatches: list[SelfReportMismatch] = []

        protected = set(contract.protected_elements)

        # --- Headings ---
        orig_headings = {(lvl, title) for lvl, title, _ in orig.headings}
        gen_headings = {(lvl, title) for lvl, title, _ in gen.headings}

        for h in orig_headings - gen_headings:
            deleted_nodes.append(
                DiffNode(
                    path=f"/headings/{h[1]}",
                    kind="heading",
                    before={"level": h[0], "title": h[1]},
                    after=None,
                    description=f"Heading '{h[1]}' (level {h[0]}) deleted.",
                    risk_hint="high",
                )
            )
            if "headings" in protected:
                protected_element_changes.append(
                    ProtectedChange(
                        element="headings",
                        path=f"/headings/{h[1]}",
                        change_type="deleted",
                        description=f"Protected heading '{h[1]}' deleted.",
                        risk_hint="high",
                    )
                )

        for h in gen_headings - orig_headings:
            added_nodes.append(
                DiffNode(
                    path=f"/headings/{h[1]}",
                    kind="heading",
                    before=None,
                    after={"level": h[0], "title": h[1]},
                    description=f"Heading '{h[1]}' (level {h[0]}) added.",
                    risk_hint="low",
                )
            )

        # --- Definitions ---
        orig_defs = {(term, body) for term, body, _ in orig.definitions}
        gen_defs = {(term, body) for term, body, _ in gen.definitions}
        orig_def_terms = {term for term, _ in orig_defs}
        gen_def_terms = {term for term, _ in gen_defs}

        for term, body in orig_defs - gen_defs:
            if term in gen_def_terms:
                gen_body = next(b for t, b in gen_defs if t == term)
                changed_nodes.append(
                    DiffNode(
                        path=f"/definitions/{term}",
                        kind="definition",
                        before=body,
                        after=gen_body,
                        description=f"Definition of '{term}' changed.",
                        risk_hint="high",
                    )
                )
                if "definitions" in protected:
                    protected_element_changes.append(
                        ProtectedChange(
                            element="definitions",
                            path=f"/definitions/{term}",
                            change_type="changed",
                            description=f"Protected definition '{term}' changed.",
                            risk_hint="high",
                        )
                    )
            else:
                deleted_nodes.append(
                    DiffNode(
                        path=f"/definitions/{term}",
                        kind="definition",
                        before=body,
                        after=None,
                        description=f"Definition of '{term}' deleted.",
                        risk_hint="high",
                    )
                )
                if "definitions" in protected:
                    protected_element_changes.append(
                        ProtectedChange(
                            element="definitions",
                            path=f"/definitions/{term}",
                            change_type="deleted",
                            description=f"Protected definition '{term}' deleted.",
                            risk_hint="critical",
                        )
                    )

        for term, body in gen_defs - orig_defs:
            if term not in orig_def_terms:
                added_nodes.append(
                    DiffNode(
                        path=f"/definitions/{term}",
                        kind="definition",
                        before=None,
                        after=body,
                        description=f"Definition of '{term}' added.",
                        risk_hint="low",
                    )
                )

        # --- Citations ---
        orig_cits = {raw for raw, _ in orig.citations}
        gen_cits = {raw for raw, _ in gen.citations}

        for cit in orig_cits - gen_cits:
            deleted_nodes.append(
                DiffNode(
                    path="/citations",
                    kind="citation",
                    before=cit,
                    after=None,
                    description=f"Citation '{cit}' deleted.",
                    risk_hint="critical",
                )
            )
            if "citations" in protected:
                protected_element_changes.append(
                    ProtectedChange(
                        element="citations",
                        path="/citations",
                        change_type="deleted",
                        description=f"Protected citation '{cit}' deleted.",
                        risk_hint="critical",
                    )
                )

        for cit in gen_cits - orig_cits:
            added_nodes.append(
                DiffNode(
                    path="/citations",
                    kind="citation",
                    before=None,
                    after=cit,
                    description=f"Citation '{cit}' added.",
                    risk_hint="low",
                )
            )

        # --- Numbers ---
        orig_nums = {val for val, _ in orig.numbers}
        gen_nums = {val for val, _ in gen.numbers}

        for num in orig_nums - gen_nums:
            changed_nodes.append(
                DiffNode(
                    path="/numbers",
                    kind="number",
                    before=num,
                    after=None,
                    description=f"Number '{num}' removed or changed.",
                    risk_hint="high",
                )
            )
            if "numbers" in protected:
                protected_element_changes.append(
                    ProtectedChange(
                        element="numbers",
                        path="/numbers",
                        change_type="changed",
                        description=f"Protected number '{num}' changed or removed.",
                        risk_hint="high",
                    )
                )

        for num in gen_nums - orig_nums:
            changed_nodes.append(
                DiffNode(
                    path="/numbers",
                    kind="number",
                    before=None,
                    after=num,
                    description=f"Number '{num}' added or changed.",
                    risk_hint="medium",
                )
            )

        # --- Dates ---
        orig_dates = {val for val, _ in orig.dates}
        gen_dates = {val for val, _ in gen.dates}

        for d in orig_dates - gen_dates:
            changed_nodes.append(
                DiffNode(
                    path="/dates",
                    kind="date",
                    before=d,
                    after=None,
                    description=f"Date '{d}' removed or changed.",
                    risk_hint="high",
                )
            )
            if "dates" in protected:
                protected_element_changes.append(
                    ProtectedChange(
                        element="dates",
                        path="/dates",
                        change_type="changed",
                        description=f"Protected date '{d}' changed or removed.",
                        risk_hint="high",
                    )
                )

        # --- Links ---
        orig_links = {(text, url) for text, url, _ in orig.links}
        gen_links = {(text, url) for text, url, _ in gen.links}

        for text, url in orig_links - gen_links:
            deleted_nodes.append(
                DiffNode(
                    path="/links",
                    kind="link",
                    before={"text": text, "url": url},
                    after=None,
                    description=f"Link '[{text}]({url})' deleted.",
                    risk_hint="medium",
                )
            )
            if "references" in protected:
                protected_element_changes.append(
                    ProtectedChange(
                        element="references",
                        path="/links",
                        change_type="deleted",
                        description=f"Protected reference link '[{text}]({url})' deleted.",
                        risk_hint="high",
                    )
                )

        # --- Code blocks ---
        orig_codes = {body for body, _ in orig.code_blocks}
        gen_codes = {body for body, _ in gen.code_blocks}

        for body in orig_codes - gen_codes:
            deleted_nodes.append(
                DiffNode(
                    path="/code_blocks",
                    kind="code_block",
                    before=body[:80],
                    after=None,
                    description="Code block deleted or changed.",
                    risk_hint="medium",
                )
            )

        for body in gen_codes - orig_codes:
            added_nodes.append(
                DiffNode(
                    path="/code_blocks",
                    kind="code_block",
                    before=None,
                    after=body[:80],
                    description="Code block added or changed.",
                    risk_hint="low",
                )
            )

        # --- Self-report mismatch detection ---
        if generator_output is not None:
            self_report_mismatches = _detect_self_report_mismatches(
                generator_output,
                protected_element_changes,
                changed_nodes,
                deleted_nodes,
            )

        return StructuralDiff(
            contract_id=contract.contract_id,
            domain="markdown",
            changed_nodes=changed_nodes,
            added_nodes=added_nodes,
            deleted_nodes=deleted_nodes,
            moved_nodes=[],
            protected_element_changes=protected_element_changes,
            schema_violations=[],
            signature_changes=[],
            reference_breaks=[],
            self_report_mismatches=self_report_mismatches,
            diff_confidence=0.9,
        )


def _detect_self_report_mismatches(
    generator_output: GeneratorOutput,
    protected_changes: list[ProtectedChange],
    changed_nodes: list[DiffNode],
    deleted_nodes: list[DiffNode],
) -> list[SelfReportMismatch]:
    mismatches: list[SelfReportMismatch] = []
    sr = generator_output.self_report
    unchanged_claimed = {e.lower() for e in sr.unchanged_elements}

    for pc in protected_changes:
        elem = pc.element.lower()
        if elem in unchanged_claimed:
            mismatches.append(
                SelfReportMismatch(
                    reported=f"{pc.element} unchanged",
                    actual=f"{pc.element} {pc.change_type}",
                    description=(
                        f"Generator claimed '{pc.element}' unchanged, "
                        f"but structural diff detected {pc.change_type} at {pc.path}."
                    ),
                    risk_hint="high",
                )
            )

    citation_kinds = {"citation", "citations"}
    number_kinds = {"number", "numbers"}

    sr_no_citations = any(
        "citation" in e.lower() for e in sr.unchanged_elements
    )
    sr_no_numbers = any(
        "number" in e.lower() for e in sr.unchanged_elements
    )

    actual_citation_deleted = any(
        n.kind in citation_kinds for n in deleted_nodes
    )
    actual_number_changed = any(
        n.kind in number_kinds for n in changed_nodes + deleted_nodes
    )

    if sr_no_citations and actual_citation_deleted:
        mismatches.append(
            SelfReportMismatch(
                reported="citations unchanged",
                actual="citation deleted",
                description=(
                    "Generator self-report claims citations unchanged, "
                    "but structural diff detected citation deletion."
                ),
                risk_hint="critical",
            )
        )

    if sr_no_numbers and actual_number_changed:
        mismatches.append(
            SelfReportMismatch(
                reported="numbers unchanged",
                actual="number changed or removed",
                description=(
                    "Generator self-report claims numbers unchanged, "
                    "but structural diff detected number change."
                ),
                risk_hint="high",
            )
        )

    return mismatches
