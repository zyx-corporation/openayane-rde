"""Filesystem adapter (Phase 5 P5-4 / #47)."""

from __future__ import annotations

from pathlib import Path

from openayane_rde import run_phase1_evaluation
from openayane_rde.adapters.filesystem import FilesystemAdapter
from openayane_rde.adapters.types import FilesystemAdapterSource
from openayane_rde.core.models import GeneratorOutput, ModelInfo, SelfReport


def test_collect_and_build_contract(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "a.md").write_text("# Hi\n", encoding="utf-8")
    adapter = FilesystemAdapter()
    src = FilesystemAdapterSource(
        root=str(root),
        relative_paths=["docs/a.md"],
        requested_action="Check doc.",
    )
    ctx = adapter.collect_context(src)
    assert ctx.files["docs/a.md"] == "# Hi\n"
    assert adapter.side_effect_profile.may_write_filesystem is False
    contract = adapter.build_contract(ctx)
    assert "docs/a.md" in contract.target_scope.files


def test_skips_path_outside_root(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    other = tmp_path / "other"
    other.mkdir()
    (other / "secret.md").write_text("x", encoding="utf-8")
    adapter = FilesystemAdapter()
    ctx = adapter.collect_context(
        FilesystemAdapterSource(
            root=str(root),
            relative_paths=["../other/secret.md"],
        )
    )
    assert ctx.files == {}
    assert any("escapes root" in n for n in ctx.notes)


def test_produce_evidence_from_evaluation(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    (root / "x.md").write_text("# T\n\nBody.\n", encoding="utf-8")
    adapter = FilesystemAdapter()
    ctx = adapter.collect_context(
        FilesystemAdapterSource(root=str(root), relative_paths=["x.md"]),
    )
    contract = adapter.build_contract(ctx)
    before = ctx.files["x.md"]
    go = GeneratorOutput(
        contract_id=contract.contract_id,
        output_type="full_text",
        payload=before,
        self_report=SelfReport(),
        model_info=ModelInfo(provider="mock", model="fs-adapter-test"),
    )
    result = run_phase1_evaluation(
        before,
        go,
        contract,
        domain="markdown",
    )
    ev = adapter.produce_evidence(result)
    assert ev.action == "make_policy_decision"
    assert ev.policy_decision_id == result.policy_decision.decision_id
