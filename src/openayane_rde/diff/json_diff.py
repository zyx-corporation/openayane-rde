"""JSON structural diff engine for OpenAyane RDE Phase 1.

Detected elements:
  - key deletion
  - key addition
  - value change
  - type change
  - required field deletion
  - schema violation if schema is provided
"""

from __future__ import annotations

import json
from typing import Any

from openayane_rde.core.models import (
    DiffNode,
    GeneratorOutput,
    ProtectedChange,
    SelfReportMismatch,
    StructuralDiff,
    TaskContract,
    Violation,
)
from openayane_rde.diff.base import StructuralDiffEngine


class JsonDiff(StructuralDiffEngine):
    """Structural diff engine for JSON documents."""

    domain = "json"

    def __init__(self, required_fields: list[str] | None = None) -> None:
        """
        Args:
            required_fields: List of top-level field names that must not be deleted.
                             If None, no required-field enforcement beyond contract.
        """
        self._required_fields: list[str] = required_fields or []

    def diff(
        self,
        original: str,
        generated: str,
        contract: TaskContract,
        generator_output: GeneratorOutput | None = None,
    ) -> StructuralDiff:
        try:
            orig_obj = json.loads(original)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to parse original JSON: {exc}") from exc
        try:
            gen_obj = json.loads(generated)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to parse generated JSON: {exc}") from exc

        protected = set(contract.protected_elements)

        changed_nodes: list[DiffNode] = []
        added_nodes: list[DiffNode] = []
        deleted_nodes: list[DiffNode] = []
        protected_element_changes: list[ProtectedChange] = []
        schema_violations: list[Violation] = []
        self_report_mismatches: list[SelfReportMismatch] = []

        _compare(
            orig_obj,
            gen_obj,
            path="",
            protected=protected,
            required_fields=self._required_fields,
            changed_nodes=changed_nodes,
            added_nodes=added_nodes,
            deleted_nodes=deleted_nodes,
            protected_element_changes=protected_element_changes,
            schema_violations=schema_violations,
        )

        if generator_output is not None:
            self_report_mismatches = _detect_self_report_mismatches(
                generator_output,
                protected_element_changes,
                deleted_nodes,
            )

        return StructuralDiff(
            contract_id=contract.contract_id,
            domain="json",
            changed_nodes=changed_nodes,
            added_nodes=added_nodes,
            deleted_nodes=deleted_nodes,
            moved_nodes=[],
            protected_element_changes=protected_element_changes,
            schema_violations=schema_violations,
            signature_changes=[],
            reference_breaks=[],
            self_report_mismatches=self_report_mismatches,
            diff_confidence=1.0,
        )


def _path(parent: str, key: str | int) -> str:
    if parent == "":
        return f"/{key}"
    return f"{parent}/{key}"


def _type_name(v: Any) -> str:
    if isinstance(v, bool):
        return "boolean"
    if isinstance(v, int):
        return "integer"
    if isinstance(v, float):
        return "number"
    if isinstance(v, str):
        return "string"
    if isinstance(v, list):
        return "array"
    if isinstance(v, dict):
        return "object"
    if v is None:
        return "null"
    return type(v).__name__


def _compare(
    orig: Any,
    gen: Any,
    path: str,
    protected: set[str],
    required_fields: list[str],
    changed_nodes: list[DiffNode],
    added_nodes: list[DiffNode],
    deleted_nodes: list[DiffNode],
    protected_element_changes: list[ProtectedChange],
    schema_violations: list[Violation],
    depth: int = 0,
) -> None:
    if type(orig) is not type(gen) and not (
        isinstance(orig, (int, float)) and isinstance(gen, (int, float))
    ):
        _record_type_change(
            orig, gen, path, protected, changed_nodes, protected_element_changes
        )
        return

    if isinstance(orig, dict):
        _compare_dicts(
            orig,
            gen,
            path,
            protected,
            required_fields if depth == 0 else [],
            changed_nodes,
            added_nodes,
            deleted_nodes,
            protected_element_changes,
            schema_violations,
            depth,
        )
    elif isinstance(orig, list):
        _compare_lists(
            orig,
            gen,
            path,
            protected,
            changed_nodes,
            added_nodes,
            deleted_nodes,
            protected_element_changes,
            schema_violations,
            depth,
        )
    else:
        if orig != gen:
            _record_value_change(orig, gen, path, protected, changed_nodes, protected_element_changes)


def _record_type_change(
    orig: Any,
    gen: Any,
    path: str,
    protected: set[str],
    changed_nodes: list[DiffNode],
    protected_element_changes: list[ProtectedChange],
) -> None:
    orig_type = _type_name(orig)
    gen_type = _type_name(gen)
    changed_nodes.append(
        DiffNode(
            path=path,
            kind="type_change",
            before=orig_type,
            after=gen_type,
            description=f"Type changed from '{orig_type}' to '{gen_type}' at {path}.",
            risk_hint="high",
        )
    )
    if "types" in protected:
        protected_element_changes.append(
            ProtectedChange(
                element="types",
                path=path,
                change_type="changed",
                description=f"Protected type changed from '{orig_type}' to '{gen_type}'.",
                risk_hint="high",
            )
        )


def _record_value_change(
    orig: Any,
    gen: Any,
    path: str,
    protected: set[str],
    changed_nodes: list[DiffNode],
    protected_element_changes: list[ProtectedChange],
) -> None:
    changed_nodes.append(
        DiffNode(
            path=path,
            kind="value_change",
            before=orig,
            after=gen,
            description=f"Value changed at {path}.",
            risk_hint="medium",
        )
    )


def _compare_dicts(
    orig: dict[str, Any],
    gen: dict[str, Any],
    path: str,
    protected: set[str],
    required_fields: list[str],
    changed_nodes: list[DiffNode],
    added_nodes: list[DiffNode],
    deleted_nodes: list[DiffNode],
    protected_element_changes: list[ProtectedChange],
    schema_violations: list[Violation],
    depth: int,
) -> None:
    orig_keys = set(orig.keys())
    gen_keys = set(gen.keys())

    for key in orig_keys - gen_keys:
        node_path = _path(path, key)
        deleted_nodes.append(
            DiffNode(
                path=node_path,
                kind="key_deletion",
                before=orig[key],
                after=None,
                description=f"Key '{key}' deleted at {node_path}.",
                risk_hint="high",
            )
        )
        if "schema_keys" in protected:
            protected_element_changes.append(
                ProtectedChange(
                    element="schema_keys",
                    path=node_path,
                    change_type="deleted",
                    description=f"Protected schema key '{key}' deleted.",
                    risk_hint="high",
                )
            )
        if key in required_fields:
            schema_violations.append(
                Violation(
                    path=node_path,
                    violation_type="required_field_deleted",
                    description=f"Required field '{key}' was deleted.",
                    risk_hint="critical",
                )
            )
            if "required_fields" in protected:
                protected_element_changes.append(
                    ProtectedChange(
                        element="required_fields",
                        path=node_path,
                        change_type="deleted",
                        description=f"Protected required field '{key}' deleted.",
                        risk_hint="critical",
                    )
                )

    for key in gen_keys - orig_keys:
        node_path = _path(path, key)
        added_nodes.append(
            DiffNode(
                path=node_path,
                kind="key_addition",
                before=None,
                after=gen[key],
                description=f"Key '{key}' added at {node_path}.",
                risk_hint="low",
            )
        )

    for key in orig_keys & gen_keys:
        node_path = _path(path, key)
        _compare(
            orig[key],
            gen[key],
            node_path,
            protected,
            [],
            changed_nodes,
            added_nodes,
            deleted_nodes,
            protected_element_changes,
            schema_violations,
            depth + 1,
        )


def _compare_lists(
    orig: list[Any],
    gen: list[Any],
    path: str,
    protected: set[str],
    changed_nodes: list[DiffNode],
    added_nodes: list[DiffNode],
    deleted_nodes: list[DiffNode],
    protected_element_changes: list[ProtectedChange],
    schema_violations: list[Violation],
    depth: int,
) -> None:
    orig_len = len(orig)
    gen_len = len(gen)
    min_len = min(orig_len, gen_len)

    for i in range(min_len):
        _compare(
            orig[i],
            gen[i],
            _path(path, i),
            protected,
            [],
            changed_nodes,
            added_nodes,
            deleted_nodes,
            protected_element_changes,
            schema_violations,
            depth + 1,
        )

    for i in range(min_len, orig_len):
        node_path = _path(path, i)
        deleted_nodes.append(
            DiffNode(
                path=node_path,
                kind="array_item_deletion",
                before=orig[i],
                after=None,
                description=f"Array item at index {i} deleted.",
                risk_hint="medium",
            )
        )

    for i in range(min_len, gen_len):
        node_path = _path(path, i)
        added_nodes.append(
            DiffNode(
                path=node_path,
                kind="array_item_addition",
                before=None,
                after=gen[i],
                description=f"Array item at index {i} added.",
                risk_hint="low",
            )
        )


def _detect_self_report_mismatches(
    generator_output: GeneratorOutput,
    protected_changes: list[ProtectedChange],
    deleted_nodes: list[DiffNode],
) -> list[SelfReportMismatch]:
    mismatches: list[SelfReportMismatch] = []
    sr = generator_output.self_report
    unchanged_claimed = {e.lower() for e in sr.unchanged_elements}

    has_schema_claim = any("schema" in e for e in unchanged_claimed)
    for pc in protected_changes:
        elem = pc.element.lower()
        if elem in unchanged_claimed or has_schema_claim:
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

    return mismatches
