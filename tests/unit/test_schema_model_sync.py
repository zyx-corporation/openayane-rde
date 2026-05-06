"""Guardrails: JSON Schema files in schemas/ stay aligned with Pydantic models.

Full structural equality between hand-written schemas and model_json_schema()
output is brittle; we assert that every ``required`` property in each schema
exists as a field on the corresponding model (spec ↔ implementation drift).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, get_args

from openayane_rde.core.models import (
    ActorKind,
    AuditActionKind,
    AuditEvent,
    ChangeType,
    ContractMode,
    DiffDomain,
    DriftPatternKind,
    GeneratorOutput,
    OutputType,
    PolicyActionKind,
    ProtectedElementKind,
    ProviderKind,
    RDEClassification,
    RDEResult,
    RelationStoreRecord,
    RelationType,
    RequiredAction,
    RiskLevel,
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


def _load_schema(name: str) -> dict[str, Any]:
    path = SCHEMAS_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_enum_at(schema: dict[str, Any], path: list[str]) -> set[str]:
    """Resolve ``path`` to either a ``{"enum": [...]}`` object or the enum list."""

    node: Any = schema
    for key in path:
        node = node[key]
    if isinstance(node, dict):
        return set(node["enum"])
    return set(node)


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


def test_relation_store_schema_required_are_fields() -> None:
    data = _load_schema("relation_store.schema.json")
    req = set(data["$defs"]["relation_store_record"]["required"])
    assert req <= _model_field_names(RelationStoreRecord)


def test_enum_task_contract_mode_matches_schema() -> None:
    data = _load_schema("task_contract.schema.json")
    schema_modes = set(data["properties"]["mode"]["enum"])
    assert schema_modes == set(get_args(ContractMode))


def test_enum_audit_event_actor_matches_schema() -> None:
    data = _load_schema("audit_event.schema.json")
    schema_actors = set(data["properties"]["actor"]["enum"])
    assert schema_actors == set(get_args(ActorKind))


def test_enum_rde_classification_matches_schema() -> None:
    data = _load_schema("rde_result.schema.json")
    assert _schema_enum_at(data, ["properties", "classification", "enum"]) == set(
        get_args(RDEClassification)
    )


def test_enum_risk_level_matches_schema() -> None:
    data = _load_schema("rde_result.schema.json")
    assert _schema_enum_at(data, ["properties", "risk_level", "enum"]) == set(
        get_args(RiskLevel)
    )


def test_enum_required_action_matches_schema() -> None:
    data = _load_schema("rde_result.schema.json")
    assert _schema_enum_at(data, ["properties", "required_action", "enum"]) == set(
        get_args(RequiredAction)
    )


def test_enum_protected_element_kind_matches_schema() -> None:
    data = _load_schema("task_contract.schema.json")
    assert _schema_enum_at(
        data, ["properties", "protected_elements", "items"]
    ) == set(get_args(ProtectedElementKind))


def test_enum_output_type_matches_schema() -> None:
    data = _load_schema("generator_output.schema.json")
    assert _schema_enum_at(data, ["properties", "output_type", "enum"]) == set(
        get_args(OutputType)
    )


def test_enum_audit_action_matches_schema() -> None:
    data = _load_schema("audit_event.schema.json")
    assert _schema_enum_at(data, ["properties", "action", "enum"]) == set(
        get_args(AuditActionKind)
    )


def test_enum_provider_kind_matches_schema() -> None:
    data = _load_schema("generator_output.schema.json")
    props = data["properties"]["model_info"]["properties"]
    assert _schema_enum_at(props, ["provider", "enum"]) == set(get_args(ProviderKind))


def test_enum_diff_domain_matches_schema() -> None:
    data = _load_schema("structural_diff.schema.json")
    assert _schema_enum_at(data, ["properties", "domain", "enum"]) == set(
        get_args(DiffDomain)
    )


def test_enum_change_type_in_structural_diff_defs_matches_schema() -> None:
    data = _load_schema("structural_diff.schema.json")
    assert _schema_enum_at(
        data, ["$defs", "protected_change", "properties", "change_type", "enum"]
    ) == set(get_args(ChangeType))


def test_enum_relation_type_matches_schema() -> None:
    data = _load_schema("relation_store.schema.json")
    assert _schema_enum_at(data, ["$defs", "relation_type", "enum"]) == set(
        get_args(RelationType)
    )


def test_enum_drift_pattern_kind_matches_schema() -> None:
    data = _load_schema("relation_store.schema.json")
    assert _schema_enum_at(data, ["$defs", "drift_pattern_kind", "enum"]) == set(
        get_args(DriftPatternKind)
    )


def test_enum_relation_store_risk_level_matches_schema() -> None:
    data = _load_schema("relation_store.schema.json")
    assert _schema_enum_at(data, ["$defs", "risk_level", "enum"]) == set(
        get_args(RiskLevel)
    )


def test_policy_action_literals_match_required_action() -> None:
    """PolicyDecision has no JSON schema yet; keep actions aligned with RDE."""

    assert set(get_args(PolicyActionKind)) == set(get_args(RequiredAction))
