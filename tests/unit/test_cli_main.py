"""Tests for Phase 5 CLI (openayane-rde)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from openayane_rde.cli.main import build_parser, main
from openayane_rde.contract.builder import build_contract


def _repo_src() -> Path:
    return Path(__file__).resolve().parents[2] / "src"


@pytest.mark.parametrize(
    "argv",
    [
        ["evaluate", "--help"],
        ["diff", "--help"],
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
