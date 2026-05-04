"""Golden fixtures for Phase 3 hardening (CI readability checks)."""

from __future__ import annotations

import json
from pathlib import Path

from openayane_rde.core.models import AuditEvent


def test_golden_execution_gate_audit_fixture_validates() -> None:
    root = Path(__file__).resolve().parents[2]
    path = root / "fixtures" / "phase3" / "golden_execution_gate_audit.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    ev = AuditEvent.model_validate(data)
    assert ev.action == "execution_gate_evaluated"
    assert ev.payload.get("evaluation_kind") == "pre_synthetic"
