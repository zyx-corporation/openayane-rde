"""GitHub PR fixture adapter (Phase 5 P5-5): diff + before/after files → RDE evidence.

No network and no posting. Operates on a local directory layout only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from openayane_rde.adapters.types import AdapterSideEffectProfile
from openayane_rde.audit.log import audit_event_policy_decision
from openayane_rde.contract.builder import build_contract
from openayane_rde.core.models import AuditEvent, GeneratorOutput, ModelInfo, SelfReport, TaskContract
from openayane_rde.runtime._flow import run_phase1_evaluation
from openayane_rde.runtime.result import Phase1EvaluationResult


def parse_git_diff_changed_paths(diff_text: str) -> list[str]:
    """Extract changed file paths from a unified ``diff --git`` document (``b/...`` side)."""

    out: list[str] = []
    seen: set[str] = set()
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4 and parts[3].startswith("b/"):
                p = parts[3][2:]
                if p not in seen:
                    seen.add(p)
                    out.append(p)
    return out


class GitHubPRAdapterSource(BaseModel):
    """Local PR fixture: ``pr.diff`` plus ``before/`` and ``after/`` trees."""

    model_config = {"extra": "forbid"}

    kind: Literal["github_pr_fixture"] = "github_pr_fixture"
    fixture_root: str
    requested_action: str = Field(
        default="Review pull-request changes under OpenAyane RDE (local fixture).",
    )
    domain: Literal["markdown", "json", "python"] = "markdown"


@dataclass
class GitHubPRReviewBundle:
    """Outcome of evaluating a PR fixture (operator-facing, auditable)."""

    changed_files: list[str]
    notes: list[str] = field(default_factory=list)
    task_contract: TaskContract | None = None
    results_by_file: dict[str, Phase1EvaluationResult] = field(default_factory=dict)
    markdown_draft: str = ""
    audit_events: list[AuditEvent] = field(default_factory=list)


class GitHubPRReviewAdapter:
    """Read-only filesystem + diff parse; never posts to GitHub."""

    def __init__(self) -> None:
        self._profile = AdapterSideEffectProfile(
            may_read_filesystem=True,
            may_write_filesystem=False,
            may_use_network=False,
        )

    @property
    def side_effect_profile(self) -> AdapterSideEffectProfile:
        return self._profile

    def run(self, source: GitHubPRAdapterSource) -> GitHubPRReviewBundle:
        root = Path(source.fixture_root).resolve()
        diff_path = root / "pr.diff"
        notes: list[str] = []
        if not diff_path.is_file():
            notes.append(f"Missing pr.diff under fixture root: {diff_path}")
            return GitHubPRReviewBundle(changed_files=[], notes=notes)

        diff_text = diff_path.read_text(encoding="utf-8")
        changed = parse_git_diff_changed_paths(diff_text)
        if not changed:
            notes.append("No changed paths parsed from pr.diff; check diff --git headers.")

        pairs: dict[str, tuple[str, str]] = {}
        for rel in changed:
            b = root / "before" / rel
            a = root / "after" / rel
            if not b.is_file() or not a.is_file():
                notes.append(f"Missing before/after file pair for: {rel}")
                continue
            try:
                pairs[rel] = (b.read_text(encoding="utf-8"), a.read_text(encoding="utf-8"))
            except OSError as exc:
                notes.append(f"Failed to read {rel}: {exc}")

        if not pairs:
            return GitHubPRReviewBundle(changed_files=changed, notes=notes)

        contract = build_contract(
            mode="preservation",
            requested_action=source.requested_action,
            files=sorted(pairs.keys()),
            protected_elements=["claims", "citations", "numbers"],
            allowed_delta_m=["sentence restructuring"],
            forbidden_delta_m=["citation removal", "numeric change"],
        )

        results: dict[str, Phase1EvaluationResult] = {}
        audits: list[AuditEvent] = []
        md_parts: list[str] = [
            "## OpenAyane RDE — PR review draft (local fixture; **not posted**)\n",
            f"- Changed files (diff): {', '.join(changed)}\n",
        ]
        if notes:
            md_parts.append("### Missing evidence / notes\n" + "\n".join(f"- {n}" for n in notes) + "\n")

        for rel, (before, after) in sorted(pairs.items()):
            go = GeneratorOutput(
                contract_id=contract.contract_id,
                output_type="full_text",
                payload=after,
                self_report=SelfReport(),
                model_info=ModelInfo(provider="local", model="github-pr-fixture"),
            )
            res = run_phase1_evaluation(
                before,
                go,
                contract,
                source.domain,
            )
            results[rel] = res
            audits.append(
                audit_event_policy_decision(
                    res.policy_decision,
                    rde_classification=res.rde_result.classification,
                )
            )
            md_parts.append(
                f"### `{rel}`\n"
                f"- RDE classification: **{res.rde_result.classification}**\n"
                f"- Risk: **{res.rde_result.risk_level}**\n"
                f"- Policy action: **{res.policy_decision.action}**\n"
            )

        return GitHubPRReviewBundle(
            changed_files=changed,
            notes=notes,
            task_contract=contract,
            results_by_file=results,
            markdown_draft="\n".join(md_parts),
            audit_events=audits,
        )
