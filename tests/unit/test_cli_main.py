"""Tests for Phase 5 CLI (openayane-rde)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from openayane_rde.audit.log import append_event
from openayane_rde.cli.main import build_parser, main
from openayane_rde.contract.builder import build_contract
from openayane_rde.core.models import RelationStoreRecord
from openayane_rde.relation.store import JSONRelationStore

from tests.unit.test_audit_log import make_event


def _repo_src() -> Path:
    return Path(__file__).resolve().parents[2] / "src"


@pytest.mark.parametrize(
    "argv",
    [
        ["evaluate", "--help"],
        ["diff", "--help"],
        ["config", "validate", "--help"],
        ["audit", "inspect", "--help"],
        ["relation", "inspect", "--help"],
        ["policy", "check", "--help"],
        ["institution", "decide", "--help"],
        ["schema", "validate", "--help"],
        ["golden", "run", "--help"],
        ["perf", "run", "--help"],
    ],
)
def test_subcommand_help_exits_zero(argv: list[str]) -> None:
    assert main(argv + ["--help"]) == 0


def test_evaluate_missing_file_exits_nonzero(tmp_path: Path) -> None:
    contract = tmp_path / "c.json"
    contract.write_text(build_contract(mode="preservation", requested_action="x").model_dump_json())
    missing = tmp_path / "nope.txt"
    code = main(
        [
            "evaluate",
            "--contract",
            str(contract),
            "--before",
            str(missing),
            "--after",
            str(missing),
        ]
    )
    assert code == 2


def test_evaluate_json_mode_smoke(tmp_path: Path) -> None:
    contract = build_contract(
        mode="preservation",
        requested_action="Keep text.",
        protected_elements=["citations"],
    )
    cp = tmp_path / "contract.json"
    cp.write_text(contract.model_dump_json())
    text = "# Hi\n\nSee [r](https://x). 1."
    before_p = tmp_path / "before.md"
    after_p = tmp_path / "after.md"
    before_p.write_text(text)
    after_p.write_text(text)
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        code = main(
            [
                "evaluate",
                "--contract",
                str(cp),
                "--before",
                str(before_p),
                "--after",
                str(after_p),
                "--json",
            ]
        )
    assert code == 0
    data = json.loads(buf.getvalue())
    assert "classification" in data
    assert "policy_action" in data


def test_diff_json_mode(tmp_path: Path) -> None:
    contract = build_contract(mode="preservation", requested_action="x")
    cp = tmp_path / "c.json"
    cp.write_text(contract.model_dump_json())
    t = "a"
    b = tmp_path / "b"
    a = tmp_path / "a"
    b.write_text(t)
    a.write_text(t)
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        code = main(["diff", "--contract", str(cp), "--before", str(b), "--after", str(a), "--json"])
    assert code == 0
    body = json.loads(buf.getvalue())
    assert "diff_id" in body


def test_parser_version() -> None:
    p = build_parser()
    with pytest.raises(SystemExit) as exc:
        p.parse_args(["--version"])
    assert exc.value.code == 0


def test_config_validate_cli(tmp_path: Path) -> None:
    cfg = tmp_path / "openayane.toml"
    cfg.write_text('[profile]\nname = "t"\n', encoding="utf-8")
    assert main(["config", "validate", "--config", str(cfg)]) == 0


def test_config_validate_cli_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.toml"
    assert main(["config", "validate", "--config", str(missing)]) == 2


def test_audit_inspect_cli_ok(tmp_path: Path) -> None:
    log = tmp_path / "a.jsonl"
    append_event(log, make_event())
    assert main(["audit", "inspect", "--log", str(log)]) == 0


def test_audit_inspect_cli_malformed_is_nonzero(tmp_path: Path) -> None:
    log = tmp_path / "bad.jsonl"
    log.write_text("{not json\n", encoding="utf-8")
    assert main(["audit", "inspect", "--log", str(log)]) == 1


def test_audit_inspect_via_openayane_config(tmp_path: Path) -> None:
    log = tmp_path / "a.jsonl"
    append_event(log, make_event())
    cfg = tmp_path / "openayane.toml"
    cfg.write_text(f'[audit]\npath = "{log.as_posix()}"\n', encoding="utf-8")
    assert main(["audit", "inspect", "--config", str(cfg)]) == 0


def test_relation_inspect_cli_json(tmp_path: Path) -> None:
    p = tmp_path / "rel.json"
    JSONRelationStore(p).upsert(RelationStoreRecord(subject_id="s", object_id="o"))
    assert main(["relation", "inspect", "--backend", "json", "--path", str(p)]) == 0


def test_openayane_rde_console_script_help() -> None:
    env = {**__import__("os").environ, "PYTHONPATH": str(_repo_src())}
    r = subprocess.run(
        [sys.executable, "-m", "openayane_rde.cli", "evaluate", "--help"],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert r.returncode == 0
    assert "evaluate" in r.stdout
