"""Unit tests for core data models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from openayane_rde.core.models import (
    AuditEvent,
    GeneratorOutput,
    ModelInfo,
    OutputPolicy,
    PolicyDecision,
    RDEResult,
    ReviewPolicy,
    ScoreDetails,
    SelfReport,
    StructuralDiff,
    TargetScope,
    TaskContract,
)
from openayane_rde.contract.builder import build_contract


# ---------------------------------------------------------------------------
# TaskContract
# ---------------------------------------------------------------------------


def make_contract(**kwargs: object) -> TaskContract:
    defaults = dict(
        mode="preservation",
        requested_action="Improve readability.",
        protected_elements=["claims", "citations"],
    )
    defaults.update(kwargs)
    return build_contract(**defaults)  # type: ignore[arg-type]


def test_task_contract_creates_with_defaults() -> None:
    tc = make_contract()
    assert tc.contract_id.startswith("tc_")
    assert tc.mode == "preservation"
    assert tc.created_at is not None


def test_task_contract_invalid_mode() -> None:
    with pytest.raises((ValidationError, ValueError)):
        build_contract(mode="invalid_mode", requested_action="x")  # type: ignore[arg-type]


def test_task_contract_protected_elements_valid() -> None:
    tc = build_contract(
        mode="preservation",
        requested_action="Improve style.",
        protected_elements=["claims", "numbers", "citations"],
    )
    assert "claims" in tc.protected_elements
    assert "numbers" in tc.protected_elements


def test_task_contract_invalid_protected_element() -> None:
    with pytest.raises((ValidationError, ValueError)):
        build_contract(
            mode="preservation",
            requested_action="x",
            protected_elements=["not_a_valid_element"],  # type: ignore[list-item]
        )


def test_task_contract_json_round_trip() -> None:
    tc = make_contract()
    data = tc.model_dump_json()
    tc2 = TaskContract.model_validate_json(data)
    assert tc2.contract_id == tc.contract_id
    assert tc2.mode == tc.mode


# ---------------------------------------------------------------------------
# GeneratorOutput
# ---------------------------------------------------------------------------


def test_generator_output_valid() -> None:
    go = GeneratorOutput(
        contract_id="tc_001",
        output_type="full_text",
        payload="some text",
        self_report=SelfReport(
            changed_elements=["style"],
            unchanged_elements=["claims"],
        ),
        model_info=ModelInfo(provider="mock", model="test"),
    )
    assert go.output_id.startswith("go_")


def test_generator_output_invalid_output_type() -> None:
    with pytest.raises(ValidationError):
        GeneratorOutput(
            contract_id="tc_001",
            output_type="unknown_type",  # type: ignore[arg-type]
            payload="",
            self_report=SelfReport(),
            model_info=ModelInfo(provider="mock", model="test"),
        )


def test_generator_output_json_serialization() -> None:
    go = GeneratorOutput(
        contract_id="tc_001",
        output_type="patch",
        payload="--- a\n+++ b",
        self_report=SelfReport(),
        model_info=ModelInfo(provider="mock", model="test"),
    )
    data = go.model_dump_json()
    go2 = GeneratorOutput.model_validate_json(data)
    assert go2.contract_id == "tc_001"


# ---------------------------------------------------------------------------
# StructuralDiff
# ---------------------------------------------------------------------------


def test_structural_diff_empty() -> None:
    sd = StructuralDiff(
        contract_id="tc_001",
        domain="markdown",
    )
    assert sd.diff_id.startswith("sdiff_")
    assert sd.changed_nodes == []
    assert sd.diff_confidence == 1.0


def test_structural_diff_invalid_domain() -> None:
    with pytest.raises(ValidationError):
        StructuralDiff(
            contract_id="tc_001",
            domain="invalid",  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------------------
# RDEResult
# ---------------------------------------------------------------------------


def test_rde_result_valid() -> None:
    result = RDEResult(
        contract_id="tc_001",
        classification="preserved",
        resonance_score=0.9,
        preservation_score=1.0,
        authorization_score=1.0,
        risk_level="low",
        violated_constraints=[],
        suspicious_elements=[],
        required_action="approve",
        explanation="All preserved.",
    )
    assert result.result_id.startswith("rde_")


def test_rde_result_invalid_classification() -> None:
    with pytest.raises(ValidationError):
        RDEResult(
            contract_id="tc_001",
            classification="unknown",  # type: ignore[arg-type]
            resonance_score=0.5,
            preservation_score=0.5,
            authorization_score=0.5,
            risk_level="low",
            violated_constraints=[],
            suspicious_elements=[],
            required_action="approve",
            explanation="",
        )


def test_rde_result_score_range() -> None:
    with pytest.raises(ValidationError):
        RDEResult(
            contract_id="tc_001",
            classification="preserved",
            resonance_score=1.5,
            preservation_score=1.0,
            authorization_score=1.0,
            risk_level="low",
            violated_constraints=[],
            suspicious_elements=[],
            required_action="approve",
            explanation="",
        )


# ---------------------------------------------------------------------------
# AuditEvent
# ---------------------------------------------------------------------------


def test_audit_event_valid() -> None:
    ev = AuditEvent(
        actor="rde",
        action="evaluate_rde",
        explanation="Test event.",
    )
    assert ev.event_id.startswith("audit_")


def test_audit_event_hash_validation() -> None:
    valid_hash = "sha256:" + "a" * 64
    ev = AuditEvent(
        actor="rde",
        action="evaluate_rde",
        explanation="Test.",
        hash_before=valid_hash,
        hash_after=valid_hash,
    )
    assert ev.hash_before == valid_hash


def test_audit_event_invalid_hash() -> None:
    with pytest.raises(ValidationError):
        AuditEvent(
            actor="rde",
            action="evaluate_rde",
            explanation="Test.",
            hash_before="not-a-valid-hash",
        )


# ---------------------------------------------------------------------------
# PolicyDecision
# ---------------------------------------------------------------------------


def test_policy_decision_valid() -> None:
    pd = PolicyDecision(
        contract_id="tc_001",
        rde_result_id="rde_001",
        action="approve",
        rationale="All preserved.",
    )
    assert pd.decision_id.startswith("pd_")
