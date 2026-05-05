"""CLI entrypoint for OpenAyane RDE (Phase 5 P5-1).

No network or external side effects by default. See ``docs/50_openayane_rde_phase5_operational_hardening_spec.md`` §6.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Callable, Literal, cast

from pydantic import ValidationError

from openayane_rde.cli.inspect_ops import summarize_audit_jsonl, summarize_relation_store
from openayane_rde.cli.regression import (
    run_golden_pytest,
    validate_repo_schemas_and_fixtures,
)
from openayane_rde.config import load_openayane_config, normalize_config_paths
from openayane_rde.perf.harness import run_perf_harness
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


def cmd_config_validate(args: argparse.Namespace) -> int:
    cfg_path = Path(args.config)
    if not cfg_path.is_file():
        return _die(f"Not a file: {cfg_path}", 2)
    try:
        cfg = load_openayane_config(cfg_path)
        normalized = normalize_config_paths(cfg, cfg_path)
    except ValueError as exc:
        return _die(str(exc), 2)
    except ValidationError as exc:
        if args.json:
            err_payload = {"ok": False, "errors": exc.errors(include_url=False)}
            print(json.dumps(err_payload, ensure_ascii=False))
        else:
            print(str(exc), file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps({"ok": True, "config": normalized.model_dump()}, ensure_ascii=False))
    else:
        print(f"OK: {cfg_path.resolve()}")
    return 0


def cmd_audit_inspect(args: argparse.Namespace) -> int:
    log_path: Path | None = Path(args.log) if args.log else None
    if args.config:
        cfg_path = Path(args.config)
        if not cfg_path.is_file():
            return _die(f"Not a file: {cfg_path}", 2)
        try:
            cfg = normalize_config_paths(load_openayane_config(cfg_path), cfg_path)
        except ValueError as exc:
            return _die(str(exc), 2)
        except ValidationError as exc:
            if args.json:
                err_payload = {"ok": False, "errors": exc.errors(include_url=False)}
                print(json.dumps(err_payload, ensure_ascii=False))
            else:
                print(str(exc), file=sys.stderr)
            return 1
        if log_path is None:
            log_path = Path(cfg.audit.path)
    if log_path is None:
        return _die("audit inspect: provide --log or --config", 2)
    if not log_path.is_file():
        return _die(f"Not a file: {log_path}", 2)

    summary = summarize_audit_jsonl(log_path)
    if args.json:
        print(json.dumps(summary, ensure_ascii=False))
    else:
        print(f"Audit log: {summary['log_path']}")
        print(f"Valid events: {summary['valid_events']}, malformed lines: {summary['malformed_lines']}")
        if summary["duplicate_event_ids"]:
            print(f"Duplicate event_id: {', '.join(summary['duplicate_event_ids'])}")
        if summary["actions"]:
            print("Actions:", json.dumps(summary["actions"], ensure_ascii=False))
        if summary["malformed_lines"] and summary["malformed"]:
            first = summary["malformed"][0]
            print(f"First malformed line {first['line']}: {first['error']}", file=sys.stderr)
    return 1 if summary["malformed_lines"] else 0


def cmd_relation_inspect(args: argparse.Namespace) -> int:
    backend: str | None = args.backend
    store_path: Path | None = Path(args.path) if args.path else None
    if args.config:
        cfg_path = Path(args.config)
        if not cfg_path.is_file():
            return _die(f"Not a file: {cfg_path}", 2)
        try:
            cfg = normalize_config_paths(load_openayane_config(cfg_path), cfg_path)
        except ValueError as exc:
            return _die(str(exc), 2)
        except ValidationError as exc:
            if args.json:
                err_payload = {"ok": False, "errors": exc.errors(include_url=False)}
                print(json.dumps(err_payload, ensure_ascii=False))
            else:
                print(str(exc), file=sys.stderr)
            return 1
        if backend is None:
            backend = cfg.relation_store.backend
        if store_path is None:
            store_path = Path(cfg.relation_store.path)
    if backend is None or store_path is None:
        return _die("relation inspect: provide --config or both --backend and --path", 2)

    try:
        summary = summarize_relation_store(backend, store_path)
    except (sqlite3.DatabaseError, sqlite3.OperationalError, OSError, ValueError) as exc:
        return _die(str(exc), 2)

    if args.json:
        print(json.dumps(summary, ensure_ascii=False))
    else:
        print(f"Relation backend: {summary['backend']} ({summary['path']})")
        print(f"Records: {summary['record_count']}")
        for rec in summary["records"][:10]:
            print(
                f"  {rec['subject_id']} -> {rec['object_id']}: "
                f"trust={rec['trust']:.3f} stability={rec['stability']:.3f} "
                f"affinity={rec['context_affinity']:.3f}"
            )
        if summary["record_count"] > 10:
            print(f"  ... and {summary['record_count'] - 10} more (use --json)")
    return 0


def cmd_schema_validate(args: argparse.Namespace) -> int:
    root = Path(args.repo_root)
    errs = validate_repo_schemas_and_fixtures(root)
    if args.json:
        print(json.dumps({"ok": not errs, "errors": errs}, ensure_ascii=False))
    else:
        for err in errs:
            print(err, file=sys.stderr)
        if not errs:
            print(f"OK: schemas and schema_fixtures under {root.resolve()}")
    return 1 if errs else 0


def cmd_golden_run(args: argparse.Namespace) -> int:
    root = Path(args.repo_root)
    extra: list[str] = list(args.pytest_args or [])
    if extra and extra[0] == "--":
        extra = extra[1:]
    code = run_golden_pytest(root, extra_args=extra or None)
    if args.json:
        print(json.dumps({"exit_code": code, "repo_root": str(root.resolve())}, ensure_ascii=False))
    return code


def cmd_perf_run(args: argparse.Namespace) -> int:
    root = Path(args.repo_root).resolve()
    report_path = Path(args.report) if args.report else None
    if report_path is not None and not report_path.is_absolute():
        report_path = root / report_path
    prev = Path.cwd()
    os.chdir(root)
    try:
        rep = run_perf_harness(iterations=args.iterations, report_path=report_path)
    finally:
        os.chdir(prev)
    if args.json:
        print(json.dumps(rep, ensure_ascii=False))
    else:
        print(f"Performance report: {rep.get('report_path', '')}")
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

    pcfg = sub.add_parser("config", help="Configuration commands.")
    pcfg_sub = pcfg.add_subparsers(dest="_config_sub", required=True)
    pcfg_val = pcfg_sub.add_parser("validate", help="Load and validate openayane.toml.")
    pcfg_val.add_argument(
        "--config",
        default="openayane.toml",
        help="Path to openayane.toml (default: ./openayane.toml).",
    )
    pcfg_val.add_argument("--json", action="store_true")
    pcfg_val.set_defaults(_handler=cmd_config_validate)

    pa = sub.add_parser("audit", help="Audit log commands.")
    pa_sub = pa.add_subparsers(dest="_audit_sub", required=True)
    pa_insp = pa_sub.add_parser(
        "inspect",
        help="Summarize audit JSONL (valid rows, malformed lines, duplicate IDs).",
    )
    pa_insp.add_argument("--log", default=None, help="Path to audit JSONL.")
    pa_insp.add_argument(
        "--config",
        default=None,
        help="openayane.toml; uses normalized [audit].path when --log is omitted.",
    )
    pa_insp.add_argument("--json", action="store_true")
    pa_insp.set_defaults(_handler=cmd_audit_inspect)

    pr = sub.add_parser("relation", help="Relation store commands.")
    pr_sub = pr.add_subparsers(dest="_relation_sub", required=True)
    pr_insp = pr_sub.add_parser(
        "inspect",
        help="Summarize relation store (JSON file or SQLite DB, read-only).",
    )
    pr_insp.add_argument(
        "--config",
        default=None,
        help="openayane.toml; supplies backend and path when flags omitted.",
    )
    pr_insp.add_argument("--backend", choices=("json", "sqlite"), default=None)
    pr_insp.add_argument("--path", default=None, help="Relation store path (file).")
    pr_insp.add_argument("--json", action="store_true")
    pr_insp.set_defaults(_handler=cmd_relation_inspect)

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
    psch_val = psch_sub.add_parser(
        "validate",
        help="Validate JSON Schema files and tests/schema_fixtures/*.valid.json.",
    )
    psch_val.add_argument(
        "--repo-root",
        default=".",
        help="Repository root containing schemas/ and tests/schema_fixtures/.",
    )
    psch_val.add_argument("--json", action="store_true")
    psch_val.set_defaults(_handler=cmd_schema_validate)

    pg = sub.add_parser("golden", help="Golden regression commands.")
    pg_sub = pg.add_subparsers(dest="_golden_sub", required=True)
    pg_run = pg_sub.add_parser(
        "run",
        help="Run golden tests, Phase 4 institution tests, and a policy halt case.",
    )
    pg_run.add_argument(
        "--repo-root",
        default=".",
        help="Repository root (pytest cwd).",
    )
    pg_run.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Extra arguments forwarded to pytest (place after --).",
    )
    pg_run.add_argument("--json", action="store_true")
    pg_run.set_defaults(_handler=cmd_golden_run)

    pperf = sub.add_parser("perf", help="Performance harness commands.")
    pperf_sub = pperf.add_subparsers(dest="_perf_sub", required=True)
    pperf_run = pperf_sub.add_parser(
        "run",
        help="Local core-path timings → .openayane/reports/perf_YYYYMMDD.json",
    )
    pperf_run.add_argument(
        "--repo-root",
        default=".",
        help="Run benchmarks with this working directory (default: .).",
    )
    pperf_run.add_argument(
        "--iterations",
        type=int,
        default=40,
        help="Iterations per benchmark (default 40).",
    )
    pperf_run.add_argument(
        "--report",
        default=None,
        help="Optional output JSON path (default: .openayane/reports/perf_<date>.json).",
    )
    pperf_run.add_argument("--json", action="store_true")
    pperf_run.set_defaults(_handler=cmd_perf_run)

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
