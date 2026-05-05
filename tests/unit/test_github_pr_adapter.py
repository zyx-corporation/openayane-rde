"""GitHub PR fixture adapter (Phase 5 P5-5 / #48)."""

from __future__ import annotations

from pathlib import Path

from openayane_rde.adapters.github_pr import (
    GitHubPRAdapterSource,
    GitHubPRReviewAdapter,
    parse_git_diff_changed_paths,
)

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "github_pr" / "minimal_markdown"


def test_parse_git_diff_paths() -> None:
    diff = (FIXTURE / "pr.diff").read_text(encoding="utf-8")
    assert parse_git_diff_changed_paths(diff) == ["README.md"]


def test_github_pr_fixture_bundle() -> None:
    adapter = GitHubPRReviewAdapter()
    assert adapter.side_effect_profile.may_use_network is False
    bundle = adapter.run(
        GitHubPRAdapterSource(fixture_root=str(FIXTURE)),
    )
    assert "README.md" in bundle.results_by_file
    assert bundle.task_contract is not None
    assert "README.md" in bundle.task_contract.target_scope.files
    assert "OpenAyane RDE" in bundle.markdown_draft
    assert len(bundle.audit_events) == 1
    assert bundle.audit_events[0].action == "make_policy_decision"


def test_missing_pair_surfaces_note(tmp_path: Path) -> None:
    root = tmp_path / "fx"
    (root / "before").mkdir(parents=True)
    (root / "after").mkdir()
    (root / "pr.diff").write_text(
        "diff --git a/MISSING.md b/MISSING.md\n--- a/MISSING.md\n+++ b/MISSING.md\n",
        encoding="utf-8",
    )
    bundle = GitHubPRReviewAdapter().run(GitHubPRAdapterSource(fixture_root=str(root)))
    assert bundle.results_by_file == {}
    assert any("Missing before/after" in n for n in bundle.notes)
