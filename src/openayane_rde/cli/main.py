"""CLI entrypoint for OpenAyane RDE (Phase 5 P5-1).

No network or external side effects by default. See ``docs/50_openayane_rde_phase5_operational_hardening_spec.md`` §6.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable, Literal, cast

from openayane_rde.core.models import GeneratorOutput, ModelInfo, SelfReport, TaskContract
from openayane_rde.runtime._flow import run_phase1_evaluation, run_structural_diff

Domain = Literal["markdown", "json", "python"]


def _domain_from_cli(domain: str) -> Domain:
    if domain == "generic":
        return "markdown"
    return cast(Domain, domain)


def _die(msg: str, code: int = 2) -> int:
    print(msg, file=sys.stderr)
    return code


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require_files(*paths: Path) -> int | None:
    for p in paths:
        if not p.is_file():
            return _die(f"Not a file: {p}", 2)
    return None


def cmd_evaluate(args: argparse.Namespace) -> int:
    contract_p = Path(args.contract)
    before_p = Path(args.before)
    after_p = Path(args.after)
    if err := _require_files(contract_p, before_p, after_p):
        return err

    domain = _domain_from_cli(args.domain)

    tc = TaskContract.model_validate_json(_read_text(contract_p))
    before = _read_text(before_p)
    after = _read_text(after_p)
    go = GeneratorOutput(
        contract_id=tc.contract_id,
        output_type="full_text",
        payload=after,
        self_report=SelfReport(),
        model_info=ModelInfo(provider="local", model="openayane-rde-cli"),
    )
    audit_path: Path | None = Path(args.audit_log) if args.audit_log else None

    result = run_phase1_evaluation(
        before,
        go,
        tc,
        domain,
        args.required_json_fields or None,
        audit_log_path=audit_path,
    )

    if args.json:
        out = {
            "classification": result.rde_result.classification,
            "risk_level": result.rde_result.risk_level,
            "policy_action": result.policy_decision.action,
            "rde_result_id": result.rde_result.result_id,
            "policy_decision_id": result.policy_decision.decision_id,
            "audit_event_id": result.audit_event.event_id if result.audit_event else None,
            "institution_rule_id": result.policy_decision.institution_rule_id,
        }
        print(json.dumps(out, ensure_ascii=False))
    else:
        print(f"RDE classification: {result.rde_result.classification}")
        print(f"Risk level: {result.rde_result.risk_level}")
        print(f"Policy action: {result.policy_decision.action}")
        print(f"rde_result_id: {result.rde_result.result_id}")
        print(f"policy_decision_id: {result.policy_decision.decision_id}")
        if result.audit_event:
            print(f"audit_event_id: {result.audit_event.event_id}")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    contract_p = Path(args.contract)
    before_p = Path(args.before)
    after_p = Path(args.after)
    if err := _require_files(contract_p, before_p, after_p):
        return err

    domain = _domain_from_cli(args.domain)

    tc = TaskContract.model_validate_json(_read_text(contract_p))
    before = _read_text(before_p)
    after = _read_text(after_p)
    go = GeneratorOutput(
        contract_id=tc.contract_id,
        output_type="full_text",
        payload=after,
        self_report=SelfReport(),
        model_info=ModelInfo(provider="local", model="openayane-rde-cli-diff"),
    )
    diff = run_structural_diff(
        before,
        go,
        tc,
        domain,
        args.required_json_fields or None,
    )
    if args.json:
        print(diff.model_dump_json())
    else:
        print(f"diff_id: {diff.diff_id}")
        print(f"changed_nodes: {len(diff.changed_nodes)}")
        print(f"domain: {diff.domain}")
    return 0


def cmd_stub(name: str, args: argparse.Namespace) -> int:
    if args.json:
        print(json.dumps({"command": name, "status": "not_implemented"}, ensure_ascii=False))
    else:
        print(f"{name}: not implemented (Phase 5 follow-up). Use --help.")
    return 0


def _stub_handler(label: str) -> Callable[[argparse.Namespace], int]:
    def _handler(args: argparse.Namespace) -> int:
        return cmd_stub(label, args)

    return _handler


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="openayane-rde",
        description="OpenAyane RDE — local evaluation and inspection CLI.",
    )
    p.add_argument(
        "--version",
        action="version",
        version="openayane-rde 0.1.0",
    )
    sub = p.add_subparsers(dest="command", required=True)

    pe = sub.add_parser("evaluate", help="Run Phase 1 evaluation (RDE + policy).")
    pe.add_argument("--contract", required=True, help="Path to TaskContract JSON.")
    pe.add_argument("--before", required=True, help="Path to original content.")
    pe.add_argument("--after", required=True, help="Path to generated content.")
    pe.add_argument(
        "--domain",
        choices=("markdown", "json", "python", "generic"),
        default="markdown",
        help="Structural diff domain (generic maps to markdown).",
    )
    pe.add_argument(
        "--audit-log",
        default=None,
        help="Optional JSONL path to append audit row.",
    )
    pe.add_argument(
        "--required-json-fields",
        nargs="*",
        default=None,
        help="For json domain: required field names.",
    )
    pe.add_argument("--json", action="store_true", help="Machine-readable summary.")
    pe.set_defaults(_handler=cmd_evaluate)

    pd = sub.add_parser("diff", help="Structural diff only (not full RDE).")
    pd.add_argument("--contract", required=True)
    pd.add_argument("--before", required=True)
    pd.add_argument("--after", required=True)
    pd.add_argument(
        "--domain",
        choices=("markdown", "json", "python", "generic"),
        default="markdown",
    )
    pd.add_argument("--required-json-fields", nargs="*", default=None)
    pd.add_argument("--json", action="store_true")
    pd.set_defaults(_handler=cmd_diff)

    pa = sub.add_parser("audit", help="Audit log commands.")
    pa_sub = pa.add_subparsers(dest="_audit_sub", required=True)
    pa_insp = pa_sub.add_parser("inspect", help="Inspect audit JSONL (stub).")
    pa_insp.add_argument("--json", action="store_true")
    pa_insp.set_defaults(_handler=_stub_handler("audit inspect"))

    pr = sub.add_parser("relation", help="Relation store commands.")
    pr_sub = pr.add_subparsers(dest="_relation_sub", required=True)
    pr_insp = pr_sub.add_parser("inspect", help="Inspect relation store (stub).")
    pr_insp.add_argument("--json", action="store_true")
    pr_insp.set_defaults(_handler=_stub_handler("relation inspect"))

    pp = sub.add_parser("policy", help="Policy commands.")
    pp_sub = pp.add_subparsers(dest="_policy_sub", required=True)
    pp_chk = pp_sub.add_parser("check", help="RDE/policy mapping without runtime (stub).")
    pp_chk.add_argument("--json", action="store_true")
    pp_chk.set_defaults(_handler=_stub_handler("policy check"))

    pi = sub.add_parser("institution", help="Institution bridge commands.")
    pi_sub = pi.add_subparsers(dest="_institution_sub", required=True)
    pi_dec = pi_sub.add_parser("decide", help="Deterministic institution over fixtures (stub).")
    pi_dec.add_argument("--json", action="store_true")
    pi_dec.set_defaults(_handler=_stub_handler("institution decide"))

    psch = sub.add_parser("schema", help="Schema commands.")
    psch_sub = psch.add_subparsers(dest="_schema_sub", required=True)
    psch_val = psch_sub.add_parser("validate", help="Validate schemas and fixtures (stub).")
    psch_val.add_argument("--json", action="store_true")
    psch_val.set_defaults(_handler=_stub_handler("schema validate"))

    pg = sub.add_parser("golden", help="Golden regression commands.")
    pg_sub = pg.add_subparsers(dest="_golden_sub", required=True)
    pg_run = pg_sub.add_parser("run", help="Run golden fixtures (stub).")
    pg_run.add_argument("--json", action="store_true")
    pg_run.set_defaults(_handler=_stub_handler("golden run"))

    pperf = sub.add_parser("perf", help="Performance harness commands.")
    pperf_sub = pperf.add_subparsers(dest="_perf_sub", required=True)
    pperf_run = pperf_sub.add_parser("run", help="Latency measurements (stub).")
    pperf_run.add_argument("--json", action="store_true")
    pperf_run.set_defaults(_handler=_stub_handler("perf run"))

    return p


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        return int(code) if isinstance(code, int) else 1

    run = cast(
        Callable[[argparse.Namespace], int] | None,
        getattr(args, "_handler", None),
    )
    if run is None:
        return _die("No command.", 2)
    return run(args)


__all__ = ["build_parser", "main"]
