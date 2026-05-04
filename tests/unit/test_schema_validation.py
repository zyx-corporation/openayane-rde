"""Schema conformance tests.

Verifies that Pydantic model serializations conform to the JSON Schema definitions
in schemas/*.schema.json.

Each model's JSON output must pass jsonschema.validate() against its schema file.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from openayane_rde.audit.hash import sha256_text
from openayane_rde.contract.builder import build_contract
from openayane_rde.core.models import (
    AuditEvent,
    ConstraintViolation,
    DiffNode,
    GeneratorOutput,
    ModelInfo,
    ProtectedChange,
    RDEResult,
    SelfReport,
    SelfReportMismatch,
    StructuralDiff,
)

SCHEMAS_DIR = Path(__file__).parent.parent.parent / "schemas"


def load_schema(name: str) -> dict:
    return json.loads((SCHEMAS_DIR / name).read_text())


def validate(instance: dict, schema: dict) -> None:
    jsonschema.validate(instance, schema)


# ---------------------------------------------------------------------------
# TaskContract
# ---------------------------------------------------------------------------


def test_task_contract_schema_conformance() -> None:
    contract = build_contract(
        mode="preservation",
        requested_action="Improve readability.",
        protected_elements=["claims", "citations", "numbers"],
        allowed_delta_m=["sentence restructuring"],
        forbidden_delta_m=["citation removal", "numeric change"],
    )
    schema = load_schema("task_contract.schema.json")
    data = json.loads(contract.model_dump_json())  # type: ignore[union-attr]
    validate(data, schema)


def test_task_contract_invalid_mode_rejected_by_schema() -> None:
    schema = load_schema("task_contract.schema.json")
    contract = build_contract(mode="preservation", requested_action="x")
    data = json.loads(contract.model_dump_json())  # type: ignore[union-attr]
    data["mode"] = "invalid_mode"
    with pytest.raises(jsonschema.ValidationError):
        validate(data, schema)


def test_task_contract_missing_required_field_rejected() -> None:
    schema = load_schema("task_contract.schema.json")
    contract = build_contract(mode="preservation", requested_action="x")
    data = json.loads(contract.model_dump_json())  # type: ignore[union-attr]
    del data["contract_id"]
    with pytest.raises(jsonschema.ValidationError):
        validate(data, schema)


# ---------------------------------------------------------------------------
# GeneratorOutput
# ---------------------------------------------------------------------------


def test_generator_output_schema_conformance() -> None:
    go = GeneratorOutput(
        contract_id="tc_001",
        output_type="patch",
        payload="--- a\n+++ b",
        self_report=SelfReport(
            changed_elements=["style"],
            unchanged_elements=["claims", "citations"],
        ),
        model_info=ModelInfo(provider="mock", model="test", temperature=None, metadata={}),
    )
    schema = load_schema("generator_output.schema.json")
    data = json.loads(go.model_dump_json())
    validate(data, schema)


def test_generator_output_invalid_output_type_rejected() -> None:
    schema = load_schema("generator_output.schema.json")
    go = GeneratorOutput(
        contract_id="tc_001",
        output_type="full_text",
        payload="text",
        self_report=SelfReport(),
        model_info=ModelInfo(provider="mock", model="test"),
    )
    data = json.loads(go.model_dump_json())
    data["output_type"] = "unknown"
    with pytest.raises(jsonschema.ValidationError):
        validate(data, schema)


def test_generator_output_invalid_provider_rejected() -> None:
    schema = load_schema("generator_output.schema.json")
    go = GeneratorOutput(
        contract_id="tc_001",
        output_type="full_text",
        payload="text",
        self_report=SelfReport(),
        model_info=ModelInfo(provider="mock", model="test"),
    )
    data = json.loads(go.model_dump_json())
    data["model_info"]["provider"] = "invalid_provider"
    with pytest.raises(jsonschema.ValidationError):
        validate(data, schema)


# ---------------------------------------------------------------------------
# StructuralDiff
# ---------------------------------------------------------------------------


def test_structural_diff_schema_conformance_empty() -> None:
    diff = StructuralDiff(contract_id="tc_001", domain="markdown")
    schema = load_schema("structural_diff.schema.json")
    data = json.loads(diff.model_dump_json())
    validate(data, schema)


def test_structural_diff_schema_conformance_with_nodes() -> None:
    diff = StructuralDiff(
        contract_id="tc_001",
        domain="python",
        changed_nodes=[
            DiffNode(
                path="/functions/run",
                kind="function_signature",
                before="def run(x: int) -> None",
                after="def run(x: int, y: int) -> None",
                description="Signature changed.",
                risk_hint="high",
            )
        ],
        protected_element_changes=[
            ProtectedChange(
                element="function_signatures",
                path="/functions/run",
                change_type="changed",
                description="Protected signature changed.",
                risk_hint="high",
            )
        ],
        self_report_mismatches=[
            SelfReportMismatch(
                reported="function signatures unchanged",
                actual="signature changed",
                description="Mismatch.",
                risk_hint="high",
            )
        ],
        diff_confidence=0.95,
    )
    schema = load_schema("structural_diff.schema.json")
    data = json.loads(diff.model_dump_json())
    validate(data, schema)


def test_structural_diff_invalid_domain_rejected() -> None:
    schema = load_schema("structural_diff.schema.json")
    diff = StructuralDiff(contract_id="tc_001", domain="markdown")
    data = json.loads(diff.model_dump_json())
    data["domain"] = "cobol"
    with pytest.raises(jsonschema.ValidationError):
        validate(data, schema)


def test_structural_diff_confidence_out_of_range_rejected() -> None:
    schema = load_schema("structural_diff.schema.json")
    diff = StructuralDiff(contract_id="tc_001", domain="markdown")
    data = json.loads(diff.model_dump_json())
    data["diff_confidence"] = 1.5
    with pytest.raises(jsonschema.ValidationError):
        validate(data, schema)


# ---------------------------------------------------------------------------
# RDEResult
# ---------------------------------------------------------------------------


def test_rde_result_schema_conformance_preserved() -> None:
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
    schema = load_schema("rde_result.schema.json")
    data = json.loads(result.model_dump_json())
    validate(data, schema)


def test_rde_result_schema_conformance_critical() -> None:
    result = RDEResult(
        contract_id="tc_001",
        classification="critical_corruption",
        resonance_score=0.1,
        preservation_score=0.2,
        authorization_score=0.1,
        risk_level="critical",
        violated_constraints=[
            ConstraintViolation(
                constraint="citations must not be deleted",
                path="/citations",
                description="Citation deleted.",
                severity="critical",
            )
        ],
        suspicious_elements=[],
        required_action="halt",
        explanation="Critical corruption detected.",
    )
    schema = load_schema("rde_result.schema.json")
    data = json.loads(result.model_dump_json())
    validate(data, schema)


def test_rde_result_invalid_classification_rejected() -> None:
    schema = load_schema("rde_result.schema.json")
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
        explanation="",
    )
    data = json.loads(result.model_dump_json())
    data["classification"] = "totally_fine"
    with pytest.raises(jsonschema.ValidationError):
        validate(data, schema)


def test_rde_result_score_out_of_range_rejected() -> None:
    schema = load_schema("rde_result.schema.json")
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
        explanation="",
    )
    data = json.loads(result.model_dump_json())
    data["resonance_score"] = 2.0
    with pytest.raises(jsonschema.ValidationError):
        validate(data, schema)


# ---------------------------------------------------------------------------
# AuditEvent
# ---------------------------------------------------------------------------


def test_audit_event_schema_conformance_minimal() -> None:
    ev = AuditEvent(
        actor="rde",
        action="evaluate_rde",
        explanation="RDE evaluated.",
    )
    schema = load_schema("audit_event.schema.json")
    data = json.loads(ev.model_dump_json())
    validate(data, schema)


def test_audit_event_schema_conformance_full() -> None:
    h = sha256_text("before")
    ev = AuditEvent(
        actor="rde",
        task_contract_id="tc_001",
        generator_output_id="go_001",
        structural_diff_id="sdiff_001",
        rde_result_id="rde_001",
        policy_decision_id="pd_001",
        action="evaluate_rde",
        hash_before=h,
        hash_after=sha256_text("after"),
        explanation="Full audit event.",
        payload={"classification": "preserved", "risk_level": "low"},
    )
    schema = load_schema("audit_event.schema.json")
    data = json.loads(ev.model_dump_json())
    validate(data, schema)


def test_audit_event_invalid_actor_rejected() -> None:
    schema = load_schema("audit_event.schema.json")
    ev = AuditEvent(actor="rde", action="evaluate_rde", explanation="test")
    data = json.loads(ev.model_dump_json())
    data["actor"] = "unknown_actor"
    with pytest.raises(jsonschema.ValidationError):
        validate(data, schema)


def test_audit_event_invalid_action_rejected() -> None:
    schema = load_schema("audit_event.schema.json")
    ev = AuditEvent(actor="rde", action="evaluate_rde", explanation="test")
    data = json.loads(ev.model_dump_json())
    data["action"] = "do_something_else"
    with pytest.raises(jsonschema.ValidationError):
        validate(data, schema)


def test_audit_event_malformed_hash_rejected() -> None:
    schema = load_schema("audit_event.schema.json")
    ev = AuditEvent(actor="rde", action="evaluate_rde", explanation="test")
    data = json.loads(ev.model_dump_json())
    data["hash_before"] = "not-a-valid-sha256"
    with pytest.raises(jsonschema.ValidationError):
        validate(data, schema)


def test_audit_event_missing_required_field_rejected() -> None:
    schema = load_schema("audit_event.schema.json")
    ev = AuditEvent(actor="rde", action="evaluate_rde", explanation="test")
    data = json.loads(ev.model_dump_json())
    del data["explanation"]
    with pytest.raises(jsonschema.ValidationError):
        validate(data, schema)
