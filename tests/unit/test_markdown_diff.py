"""Unit tests for MarkdownDiff."""

from __future__ import annotations

from openayane_rde.contract.builder import build_contract
from openayane_rde.core.models import GeneratorOutput, ModelInfo, SelfReport
from openayane_rde.diff.markdown_diff import MarkdownDiff


def make_contract(**kwargs: object) -> object:
    defaults = dict(
        mode="preservation",
        requested_action="Improve readability.",
        protected_elements=["claims", "citations", "numbers", "definitions", "headings"],
    )
    defaults.update(kwargs)
    return build_contract(**defaults)  # type: ignore[arg-type]


def make_go(payload: str, unchanged: list[str] | None = None) -> GeneratorOutput:
    return GeneratorOutput(
        contract_id="tc_test",
        output_type="full_text",
        payload=payload,
        self_report=SelfReport(unchanged_elements=unchanged or []),
        model_info=ModelInfo(provider="mock", model="test"),
    )


engine = MarkdownDiff()


# ---------------------------------------------------------------------------
# Headings
# ---------------------------------------------------------------------------


def test_heading_deletion_detected() -> None:
    orig = "# Introduction\n\nSome text.\n\n## Background\n\nMore text."
    gen = "# Introduction\n\nSome text."
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    deleted_titles = [n.before.get("title") for n in result.deleted_nodes if n.kind == "heading"]
    assert "Background" in deleted_titles


def test_heading_deletion_protected_change() -> None:
    orig = "# Main\n\nText.\n\n## Sub\n\nMore."
    gen = "# Main\n\nText."
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    protected_headings = [
        pc for pc in result.protected_element_changes if pc.element == "headings"
    ]
    assert len(protected_headings) >= 1


def test_heading_addition() -> None:
    orig = "# Main\n\nText."
    gen = "# Main\n\nText.\n\n## New Section\n\nMore."
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    added_titles = [n.after.get("title") for n in result.added_nodes if n.kind == "heading"]
    assert "New Section" in added_titles


# ---------------------------------------------------------------------------
# Citations
# ---------------------------------------------------------------------------


def test_citation_deletion_detected() -> None:
    orig = "See [Smith 2020](https://example.com) for details."
    gen = "See the reference for details."
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    deleted = [n for n in result.deleted_nodes if n.kind == "citation"]
    assert len(deleted) >= 1


def test_citation_deletion_protected_change() -> None:
    orig = "Ref: [1] supports this claim."
    gen = "This is supported."
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    protected = [pc for pc in result.protected_element_changes if pc.element == "citations"]
    assert len(protected) >= 1


# ---------------------------------------------------------------------------
# Definitions
# ---------------------------------------------------------------------------


def test_definition_change_detected() -> None:
    orig = "**RDE**: A resonant deviation evaluator.\n\nText."
    gen = "**RDE**: A policy enforcement tool.\n\nText."
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    changed = [n for n in result.changed_nodes if n.kind == "definition"]
    assert len(changed) >= 1


def test_definition_change_protected() -> None:
    orig = "**OpenAyane**: Agent safety framework.\n\nText."
    gen = "**OpenAyane**: A productivity tool.\n\nText."
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    protected = [pc for pc in result.protected_element_changes if pc.element == "definitions"]
    assert len(protected) >= 1


# ---------------------------------------------------------------------------
# Numbers
# ---------------------------------------------------------------------------


def test_number_change_detected() -> None:
    orig = "The threshold is 0.85."
    gen = "The threshold is 0.72."
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    changed_nums = [n for n in result.changed_nodes if n.kind == "number"]
    assert len(changed_nums) >= 1


def test_number_change_protected() -> None:
    orig = "Value is 42."
    gen = "Value is 100."
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    protected = [pc for pc in result.protected_element_changes if pc.element == "numbers"]
    assert len(protected) >= 1


# ---------------------------------------------------------------------------
# Self-report mismatch
# ---------------------------------------------------------------------------


def test_self_report_mismatch_citation() -> None:
    orig = "See [1] for the proof."
    gen = "See the proof."
    contract = make_contract()
    go = make_go(gen, unchanged=["citations"])
    result = engine.diff(orig, gen, contract, generator_output=go)

    mismatches = result.self_report_mismatches
    assert any("citation" in m.reported.lower() for m in mismatches)


def test_self_report_mismatch_numbers() -> None:
    orig = "The score is 0.95."
    gen = "The score is 0.80."
    contract = make_contract()
    go = make_go(gen, unchanged=["numbers"])
    result = engine.diff(orig, gen, contract, generator_output=go)

    mismatches = result.self_report_mismatches
    assert any("number" in m.reported.lower() for m in mismatches)


# ---------------------------------------------------------------------------
# No change
# ---------------------------------------------------------------------------


def test_no_change() -> None:
    text = "# Title\n\nSome content with [ref](url) and value 42."
    contract = make_contract()
    result = engine.diff(text, text, contract)

    assert result.protected_element_changes == []
    assert result.changed_nodes == []
    assert result.deleted_nodes == []
