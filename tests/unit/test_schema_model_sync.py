"""Guardrails: JSON Schema files in schemas/ stay aligned with Pydantic models.

Full structural equality between hand-written schemas and model_json_schema()
output is brittle; we assert that every ``required`` property in each schema
exists as a field on the corresponding model (spec ↔ implementation drift).
"""

from __future__ import annotations

import json
from pathlib import Path

from openayane_rde.core.models import (
    AuditEvent,
    GeneratorOutput,
    RDEResult,
    StructuralDiff,
    TaskContract,
)

SCHEMAS_DIR = Path(__file__).parent.parent.parent / "schemas"


def _required_props(schema_name: str) -> set[str]:
    path = SCHEMAS_DIR / schema_name
    data = json.loads(path.read_text(encoding="utf-8"))
    return set(data["required"])


def _model_field_names(model: type) -> set[str]:
    return set(model.model_fields.keys())


def test_task_contract_schema_required_are_fields() -> None:
    req = _required_props("task_contract.schema.json")
    assert req <= _model_field_names(TaskContract)


def test_generator_output_schema_required_are_fields() -> None:
    req = _required_props("generator_output.schema.json")
    assert req <= _model_field_names(GeneratorOutput)


def test_structural_diff_schema_required_are_fields() -> None:
    req = _required_props("structural_diff.schema.json")
    assert req <= _model_field_names(StructuralDiff)


def test_rde_result_schema_required_are_fields() -> None:
    req = _required_props("rde_result.schema.json")
    assert req <= _model_field_names(RDEResult)


def test_audit_event_schema_required_are_fields() -> None:
    req = _required_props("audit_event.schema.json")
    assert req <= _model_field_names(AuditEvent)


def test_enum_task_contract_mode_matches_schema() -> None:
    path = SCHEMAS_DIR / "task_contract.schema.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    schema_modes = set(data["properties"]["mode"]["enum"])
    from typing import get_args

    from openayane_rde.core.models import ContractMode

    py_modes = set(get_args(ContractMode))
    assert schema_modes == py_modes


def test_enum_audit_event_actor_matches_schema() -> None:
    path = SCHEMAS_DIR / "audit_event.schema.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    schema_actors = set(data["properties"]["actor"]["enum"])
    from typing import get_args

    from openayane_rde.core.models import ActorKind

    assert schema_actors == set(get_args(ActorKind))
