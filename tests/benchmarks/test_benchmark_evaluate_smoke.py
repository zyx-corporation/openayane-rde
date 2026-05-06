"""Smoke test for ``benchmarks/evaluate.py``."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EVALUATE = REPO_ROOT / "benchmarks" / "evaluate.py"


def test_evaluate_py_produces_report(tmp_path: Path) -> None:
    out = tmp_path / "report.json"
    cp = subprocess.run(
        [sys.executable, str(EVALUATE), "--repo-root", str(REPO_ROOT), "-o", str(out)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert cp.returncode == 0, cp.stderr
    data = json.loads(out.read_text())
    assert data["report_version"] == "1"
    assert "metrics" in data
    assert data["metrics"]["cases_total"] >= 1
    assert len(data["cases"]) == data["metrics"]["cases_total"]
