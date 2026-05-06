"""Representative JSON instances must validate against schemas/*.schema.json."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

SCHEMAS_DIR = Path(__file__).parent.parent.parent / "schemas"
FIXTURES_DIR = Path(__file__).parent.parent / "schema_fixtures"

_FIXTURES = [
    "task_contract",
    "generator_output",
    "structural_diff",
    "rde_result",
    "audit_event",
    "relation_store",
]


@pytest.mark.parametrize("name", _FIXTURES)
def test_fixture_validates_against_schema(name: str) -> None:
    schema = json.loads((SCHEMAS_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))
    instance = json.loads((FIXTURES_DIR / f"{name}.valid.json").read_text(encoding="utf-8"))
    jsonschema.validate(instance, schema)
