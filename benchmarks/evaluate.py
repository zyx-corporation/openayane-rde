#!/usr/bin/env python3
"""Phase 6 benchmark harness: run fixtures and emit a machine-readable JSON report.

This script does **not** claim statistical validity beyond the fixtures it enumerates.
Run from the repository root::

    python benchmarks/evaluate.py --repo-root .

Requires the package and test helpers importable (``pip install -e '.[dev]'`` or ``PYTHONPATH=.``).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from subprocess import run
from typing import Any, Literal

# Repo root on sys.path for ``tests.*`` imports when executed as a file.
_REPO_ROOT_FOR_IMPORT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT_FOR_IMPORT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT_FOR_IMPORT))

from openayane_rde.diff.json_diff import JsonDiff
from openayane_rde.diff.markdown_diff import MarkdownDiff
from openayane_rde.diff.python_ast_diff import PythonAstDiff
from openayane_rde.policy.bridge import decide_policy
from openayane_rde.rde.core import evaluate_rde
from openayane_rde.semantic.stub import semantic_delta_stub

from tests.golden.test_golden import (
    load_contract,
    load_expected,
    load_self_report,
    make_go,
)


@dataclass
class CaseResult:
    case_id: str
    category: str
    fixture: str
    kind: Literal["single", "long_chain_step"]
    step: str | None
    domain: str
    expected_classification: str
    actual_classification: str
    classification_match: bool
    expected_action: str
    actual_action: str
    action_match: bool
    expected_risk_level: str | None
    actual_risk_level: str | None
    risk_match: bool | None


def _git_head(repo_root: Path) -> str | None:
    try:
        cp = run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return cp.stdout.strip()
    except (OSError, FileNotFoundError):
        return None


def _detect_domain_and_files(fixture_dir: Path) -> tuple[str, str, str]:
    if (fixture_dir / "original.md").exists():
        return "markdown", "original.md", "modified.md"
    if (fixture_dir / "original.json").exists():
        return "json", "original.json", "modified.json"
    if (fixture_dir / "original.py").exists():
        return "python", "original.py", "modified.py"
    raise FileNotFoundError(
        f"No original.{{md,json,py}} under {fixture_dir}"
    )


def _run_rde(
    fixture_dir: Path,
    domain: str,
    original_file: str,
    modified_file: str,
    required_json_fields: list[str] | None,
) -> tuple[str, str, str]:
    contract = load_contract(fixture_dir)
    original = (fixture_dir / original_file).read_text()
    modified = (fixture_dir / modified_file).read_text()
    self_report = load_self_report(fixture_dir)
    go = make_go(contract.contract_id, modified, self_report=self_report)

    if domain == "markdown":
        engine: MarkdownDiff | JsonDiff | PythonAstDiff = MarkdownDiff()
    elif domain == "json":
        engine = JsonDiff(required_fields=required_json_fields or [])
    elif domain == "python":
        engine = PythonAstDiff()
    else:
        raise ValueError(f"Unknown domain: {domain}")

    diff = engine.diff(original, modified, contract, go)
    semantic = semantic_delta_stub(diff, contract)
    rde_result = evaluate_rde(
        contract=contract,
        generator_output=go,
        structural_diff=diff,
        semantic_delta=semantic,
    )
    policy_decision = decide_policy(rde_result, contract)
    return rde_result.classification, policy_decision.action, rde_result.risk_level


def _discover_units(benchmark_root: Path) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    for cat_dir in sorted(benchmark_root.iterdir()):
        if not cat_dir.is_dir() or cat_dir.name.startswith("."):
            continue
        for fix_dir in sorted(cat_dir.iterdir()):
            if not fix_dir.is_dir():
                continue
            chain_path = fix_dir / "chain.json"
            if chain_path.is_file():
                meta = json.loads(chain_path.read_text())
                for step in meta["steps"]:
                    units.append(
                        {
                            "category": cat_dir.name,
                            "fixture": fix_dir.name,
                            "kind": "long_chain_step",
                            "step": step,
                        }
                    )
            elif (fix_dir / "task_contract.json").is_file():
                units.append(
                    {
                        "category": cat_dir.name,
                        "fixture": fix_dir.name,
                        "kind": "single",
                        "step": None,
                    }
                )
    return units


def _run_unit(
    repo_root: Path,
    unit: dict[str, Any],
) -> CaseResult:
    benchmark_root = repo_root / "benchmarks"
    category = unit["category"]
    fixture = unit["fixture"]
    fix_dir = benchmark_root / category / fixture

    if unit["kind"] == "long_chain_step":
        step = unit["step"]
        assert step is not None
        domain, orig_f, _ = _detect_domain_and_files(fix_dir)
        mod_dir = fix_dir / step
        mod_f = f"modified{Path(orig_f).suffix}"
        if not (mod_dir / mod_f).is_file():
            raise FileNotFoundError(f"Missing {mod_dir / mod_f}")
        contract = load_contract(fix_dir)
        required = (
            contract.metadata.get("required_fields", [])
            if domain == "json"
            else None
        )
        original = (fix_dir / orig_f).read_text()
        modified = (mod_dir / mod_f).read_text()
        self_report = load_self_report(fix_dir)
        go = make_go(contract.contract_id, modified, self_report=self_report)
        if domain == "markdown":
            engine = MarkdownDiff()
        elif domain == "json":
            engine = JsonDiff(required_fields=required or [])
        else:
            engine = PythonAstDiff()
        diff = engine.diff(original, modified, contract, go)
        semantic = semantic_delta_stub(diff, contract)
        rde_result = evaluate_rde(
            contract=contract,
            generator_output=go,
            structural_diff=diff,
            semantic_delta=semantic,
        )
        policy_decision = decide_policy(rde_result, contract)
        actual_c = rde_result.classification
        actual_a = policy_decision.action
        actual_r = rde_result.risk_level
        expected = load_expected(mod_dir)
        case_id = f"{category}/{fixture}/{step}"
    else:
        domain, orig_f, mod_f = _detect_domain_and_files(fix_dir)
        contract = load_contract(fix_dir)
        required = (
            contract.metadata.get("required_fields", [])
            if domain == "json"
            else None
        )
        actual_c, actual_a, actual_r = _run_rde(
            fix_dir, domain, orig_f, mod_f, required
        )
        expected = load_expected(fix_dir)
        case_id = f"{category}/{fixture}"

    exp_c = expected["classification"]
    exp_a = expected["required_action"]
    exp_r = expected.get("risk_level")

    risk_match: bool | None = None
    if exp_r is not None:
        risk_match = actual_r == exp_r

    return CaseResult(
        case_id=case_id,
        category=category,
        fixture=fixture,
        kind=unit["kind"],
        step=unit.get("step"),
        domain=domain,
        expected_classification=exp_c,
        actual_classification=actual_c,
        classification_match=actual_c == exp_c,
        expected_action=exp_a,
        actual_action=actual_a,
        action_match=actual_a == exp_a,
        expected_risk_level=exp_r,
        actual_risk_level=actual_r,
        risk_match=risk_match,
    )


def _aggregate(results: list[CaseResult]) -> dict[str, Any]:
    n = len(results)
    cls_ok = sum(1 for r in results if r.classification_match)
    act_ok = sum(1 for r in results if r.action_match)
    risk_scored = [r for r in results if r.risk_match is not None]
    risk_ok = sum(1 for r in risk_scored if r.risk_match)

    by_domain: dict[str, dict[str, int]] = {}
    for r in results:
        bucket = by_domain.setdefault(r.domain, {"total": 0, "classification_match": 0})
        bucket["total"] += 1
        bucket["classification_match"] += int(r.classification_match)

    return {
        "cases_total": n,
        "classification_agreement_count": cls_ok,
        "classification_agreement_rate": cls_ok / n if n else 0.0,
        "policy_action_agreement_count": act_ok,
        "policy_action_agreement_rate": act_ok / n if n else 0.0,
        "risk_level_scored_cases": len(risk_scored),
        "risk_level_agreement_count": risk_ok,
        "risk_level_agreement_rate": risk_ok / len(risk_scored) if risk_scored else None,
        "by_domain": by_domain,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="OpenAyane RDE repository root (default: parent of benchmarks/).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write JSON report to this path (default: stdout only).",
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    benchmark_root = repo_root / "benchmarks"
    if not benchmark_root.is_dir():
        print(f"Missing benchmarks directory: {benchmark_root}", file=sys.stderr)
        return 2

    units = _discover_units(benchmark_root)
    if not units:
        print("No benchmark units discovered.", file=sys.stderr)
        return 3

    results: list[CaseResult] = []
    for unit in units:
        results.append(_run_unit(repo_root, unit))

    metrics = _aggregate(results)
    report: dict[str, Any] = {
        "report_version": "1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_head(repo_root),
        "repo_root": str(repo_root),
        "disclaimer": (
            "Metrics apply only to Phase 6 benchmark fixtures discovered under "
            "benchmarks/ by this script. No population inference or external validity is implied."
        ),
        "metrics": metrics,
        "metric_definitions_ref": "benchmarks/METRICS.md",
        "cases": [asdict(r) for r in results],
    }

    text = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n")
    print(text)

    all_ok = all(r.classification_match and r.action_match for r in results)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
