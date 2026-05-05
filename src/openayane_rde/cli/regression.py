"""CLI helpers for schema/fixture validation and golden regression (Phase 5 P5-7)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import jsonschema  # type: ignore[import-untyped]
from jsonschema import validators

# Mirrors tests/unit/test_schema_fixtures.py
_SCHEMA_FIXTURE_NAMES = (
    "task_contract",
    "generator_output",
    "structural_diff",
    "rde_result",
    "audit_event",
)


def _repo_root(root: Path) -> Path:
    return root.resolve()


def validate_repo_schemas_and_fixtures(root: Path) -> list[str]:
    """Return a list of human-readable errors (empty => success)."""

    errors: list[str] = []
    schemas_dir = _repo_root(root) / "schemas"
    fixtures_dir = _repo_root(root) / "tests" / "schema_fixtures"
    if not schemas_dir.is_dir():
        return [f"Missing schemas directory: {schemas_dir}"]

    for path in sorted(schemas_dir.glob("*.schema.json")):
        try:
            schema_obj: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
            cls = validators.validator_for(schema_obj)
            cls.check_schema(schema_obj)
        except (json.JSONDecodeError, jsonschema.SchemaError) as exc:
            errors.append(f"Schema invalid ({path.name}): {exc}")

    for name in _SCHEMA_FIXTURE_NAMES:
        schema_path = schemas_dir / f"{name}.schema.json"
        inst_path = fixtures_dir / f"{name}.valid.json"
        if not schema_path.is_file():
            errors.append(f"Missing schema file for fixture set: {schema_path.name}")
            continue
        if not inst_path.is_file():
            errors.append(f"Missing fixture instance: {inst_path}")
            continue
        try:
            schema_obj = json.loads(schema_path.read_text(encoding="utf-8"))
            instance = json.loads(inst_path.read_text(encoding="utf-8"))
            jsonschema.validate(instance, schema_obj)
        except (json.JSONDecodeError, jsonschema.ValidationError) as exc:
            errors.append(f"Fixture '{name}' does not validate: {exc}")

    return errors


def default_golden_pytest_targets() -> list[str]:
    """Curated regression targets: golden + Phase 4 institution + policy halt."""

    return [
        "tests/golden",
        "tests/unit/test_phase4_policy_institution.py",
        "tests/unit/test_policy_bridge.py::test_critical_corruption_always_halts",
    ]


def run_golden_pytest(repo_root: Path, extra_args: list[str] | None = None) -> int:
    """Run pytest on golden-related paths; propagate exit code."""

    cmd = [sys.executable, "-m", "pytest", "-q", *default_golden_pytest_targets()]
    if extra_args:
        cmd.extend(extra_args)
    return int(subprocess.call(cmd, cwd=str(_repo_root(repo_root))))
