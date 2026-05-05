"""Unit tests for AuditLog JSONL writer and hash utilities."""

from __future__ import annotations

import tempfile
from pathlib import Path


from openayane_rde.audit.hash import sha256_text
from openayane_rde.audit.log import append_event, audit_event_policy_decision, load_events
from openayane_rde.core.models import AuditEvent, PolicyDecision


def make_event(**kwargs: object) -> AuditEvent:
    defaults: dict[str, object] = dict(
        actor="rde",
        action="evaluate_rde",
        explanation="Test event.",
    )
    defaults.update(kwargs)
    return AuditEvent(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# hash utilities
# ---------------------------------------------------------------------------


def test_sha256_prefix() -> None:
    result = sha256_text("hello")
    assert result.startswith("sha256:")
    assert len(result) == 71


def test_sha256_deterministic() -> None:
    assert sha256_text("same") == sha256_text("same")


def test_sha256_differs() -> None:
    assert sha256_text("before") != sha256_text("after")


# ---------------------------------------------------------------------------
# append and load
# ---------------------------------------------------------------------------


def test_append_and_load_single_event() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "events.jsonl"
        ev = make_event()
        append_event(path, ev)

        loaded = load_events(path)
        assert len(loaded) == 1
        assert loaded[0].event_id == ev.event_id
        assert loaded[0].actor == "rde"


def test_append_multiple_events() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "events.jsonl"
        ids = []
        for i in range(3):
            ev = make_event(task_contract_id=f"tc_{i:03d}")
            append_event(path, ev)
            ids.append(ev.event_id)

        loaded = load_events(path)
        assert len(loaded) == 3
        assert [e.event_id for e in loaded] == ids


def test_load_empty_file_returns_empty_list() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "events.jsonl"
        path.touch()
        loaded = load_events(path)
        assert loaded == []


def test_load_nonexistent_file_returns_empty_list() -> None:
    loaded = load_events("/tmp/nonexistent_openayane_test.jsonl")
    assert loaded == []


def test_event_round_trip_preserves_ids() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "events.jsonl"
        ev = make_event(
            task_contract_id="tc_001",
            rde_result_id="rde_001",
            policy_decision_id="pd_001",
            hash_before="sha256:" + "a" * 64,
            hash_after="sha256:" + "b" * 64,
        )
        append_event(path, ev)
        loaded = load_events(path)

        assert loaded[0].task_contract_id == "tc_001"
        assert loaded[0].rde_result_id == "rde_001"
        assert loaded[0].policy_decision_id == "pd_001"
        assert loaded[0].hash_before == "sha256:" + "a" * 64
        assert loaded[0].hash_after == "sha256:" + "b" * 64


def test_parent_directory_created_automatically() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "subdir" / "nested" / "events.jsonl"
        ev = make_event()
        append_event(path, ev)

        assert path.exists()
        loaded = load_events(path)
        assert len(loaded) == 1


def test_audit_policy_decision_splits_rde_and_institution_payload() -> None:
    pd = PolicyDecision(
        contract_id="tc_1",
        rde_result_id="rde_1",
        action="human_review",
        rationale="Combined rationale.",
        institution_rule_id="rule_pub",
        institutional_rationale="Org rule requires review.",
    )
    ev = audit_event_policy_decision(pd, rde_classification="preserved")
    assert ev.action == "make_policy_decision"
    assert ev.policy_decision_id == pd.decision_id
    assert ev.payload["rde_classification"] == "preserved"
    assert ev.payload["institution_rule_id"] == "rule_pub"
    assert ev.payload["institutional_rationale"] == "Org rule requires review."


def test_audit_policy_decision_payload_allows_null_institution_fields() -> None:
    pd = PolicyDecision(
        contract_id="tc_2",
        rde_result_id="rde_2",
        action="approve",
        rationale="RDE-only path.",
    )
    ev = audit_event_policy_decision(pd, rde_classification="preserved")
    assert ev.payload["institution_rule_id"] is None
    assert ev.payload["institutional_rationale"] is None
