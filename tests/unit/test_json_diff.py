"""Unit tests for JsonDiff."""

from __future__ import annotations

import json

import pytest

from openayane_rde.contract.builder import build_contract
from openayane_rde.diff.json_diff import JsonDiff


def make_contract(**kwargs: object) -> object:
    defaults = dict(
        mode="preservation",
        requested_action="Validate JSON schema.",
        protected_elements=["schema_keys", "required_fields", "types"],
    )
    defaults.update(kwargs)
    return build_contract(**defaults)  # type: ignore[arg-type]


engine = JsonDiff(required_fields=["name", "version", "status"])


def to_json(obj: object) -> str:
    return json.dumps(obj)


# ---------------------------------------------------------------------------
# Key deletion
# ---------------------------------------------------------------------------


def test_required_key_deletion_detected() -> None:
    orig = to_json({"name": "alice", "version": "1.0", "status": "active"})
    gen = to_json({"name": "alice", "version": "1.0"})
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    deleted_keys = [n.path for n in result.deleted_nodes if n.kind == "key_deletion"]
    assert any("status" in k for k in deleted_keys)


def test_required_key_deletion_schema_violation() -> None:
    orig = to_json({"name": "alice", "version": "1.0", "status": "active"})
    gen = to_json({"name": "alice", "version": "1.0"})
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    violations = [v for v in result.schema_violations if "required_field" in v.violation_type]
    assert len(violations) >= 1


def test_required_field_protected_change() -> None:
    orig = to_json({"name": "alice", "version": "1.0", "status": "active"})
    gen = to_json({"name": "alice", "version": "1.0"})
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    protected = [pc for pc in result.protected_element_changes if pc.element == "required_fields"]
    assert len(protected) >= 1


# ---------------------------------------------------------------------------
# Type change
# ---------------------------------------------------------------------------


def test_type_change_detected() -> None:
    orig = to_json({"count": 5})
    gen = to_json({"count": "five"})
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    type_changes = [n for n in result.changed_nodes if n.kind == "type_change"]
    assert len(type_changes) >= 1


def test_type_change_protected() -> None:
    orig = to_json({"enabled": True})
    gen = to_json({"enabled": "yes"})
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    protected = [pc for pc in result.protected_element_changes if pc.element == "types"]
    assert len(protected) >= 1


# ---------------------------------------------------------------------------
# Key addition
# ---------------------------------------------------------------------------


def test_key_addition_detected() -> None:
    orig = to_json({"name": "alice"})
    gen = to_json({"name": "alice", "extra": "bonus"})
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    added = [n for n in result.added_nodes if n.kind == "key_addition"]
    assert any("extra" in n.path for n in added)


# ---------------------------------------------------------------------------
# Value change
# ---------------------------------------------------------------------------


def test_value_change_detected() -> None:
    orig = to_json({"score": 0.95})
    gen = to_json({"score": 0.70})
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    changed = [n for n in result.changed_nodes if n.kind == "value_change"]
    assert len(changed) >= 1


# ---------------------------------------------------------------------------
# Nested structure
# ---------------------------------------------------------------------------


def test_nested_key_deletion() -> None:
    orig = to_json({"meta": {"author": "alice", "version": "1"}})
    gen = to_json({"meta": {"author": "alice"}})
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    deleted = [n for n in result.deleted_nodes if n.kind == "key_deletion"]
    assert any("version" in n.path for n in deleted)


# ---------------------------------------------------------------------------
# No change
# ---------------------------------------------------------------------------


def test_no_change() -> None:
    obj = {"name": "test", "version": "1.0", "status": "ok"}
    orig = to_json(obj)
    contract = make_contract()
    result = engine.diff(orig, orig, contract)

    assert result.changed_nodes == []
    assert result.deleted_nodes == []
    assert result.added_nodes == []
    assert result.protected_element_changes == []


# ---------------------------------------------------------------------------
# Invalid JSON
# ---------------------------------------------------------------------------


def test_invalid_json_raises() -> None:
    with pytest.raises(ValueError):
        engine.diff("not json", "{}", make_contract())
