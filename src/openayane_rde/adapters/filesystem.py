"""Filesystem adapter MVP: local paths → TaskContract + policy audit row."""

from __future__ import annotations

from pathlib import Path

from openayane_rde.adapters.types import (
    AdapterContext,
    AdapterSideEffectProfile,
    FilesystemAdapterSource,
)
from openayane_rde.audit.log import audit_event_policy_decision
from openayane_rde.contract.builder import build_contract
from openayane_rde.core.models import AuditEvent, TaskContract
from openayane_rde.runtime.result import Phase1EvaluationResult


class FilesystemAdapter:
    """Collect UTF-8 text from ``root``/relative paths and build a preservation contract."""

    def __init__(self) -> None:
        self._profile = AdapterSideEffectProfile(
            may_read_filesystem=True,
            may_write_filesystem=False,
            may_use_network=False,
        )

    @property
    def side_effect_profile(self) -> AdapterSideEffectProfile:
        return self._profile

    def collect_context(self, source: FilesystemAdapterSource) -> AdapterContext:
        root = Path(source.root).resolve()
        files: dict[str, str] = {}
        notes: list[str] = []
        if not source.relative_paths:
            notes.append("No relative_paths provided; contract target scope will be empty.")

        for rel in source.relative_paths:
            p = (root / rel).resolve()
            try:
                p.relative_to(root)
            except ValueError:
                notes.append(f"Path escapes root (skipped): {rel}")
                continue
            if not p.is_file():
                notes.append(f"Not a file (skipped): {rel}")
                continue
            try:
                files[rel] = p.read_text(encoding="utf-8")
            except OSError as exc:
                notes.append(f"Failed to read {rel}: {exc}")

        return AdapterContext(
            source_kind=source.kind,
            files=files,
            notes=notes,
            domain=source.domain,
            requested_action=source.requested_action,
        )

    def build_contract(self, context: AdapterContext) -> TaskContract:
        return build_contract(
            mode="preservation",
            requested_action=context.requested_action,
            files=sorted(context.files.keys()),
            protected_elements=["claims", "citations", "numbers"],
            allowed_delta_m=["sentence restructuring"],
            forbidden_delta_m=["citation removal", "numeric change"],
        )

    def produce_evidence(self, result: Phase1EvaluationResult) -> AuditEvent:
        return audit_event_policy_decision(
            result.policy_decision,
            rde_classification=result.rde_result.classification,
        )
