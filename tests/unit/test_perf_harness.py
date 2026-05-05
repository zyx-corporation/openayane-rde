"""Perf harness smoke (Phase 5 P5-8)."""

from __future__ import annotations

from pathlib import Path

from openayane_rde.perf.harness import run_perf_harness


def test_perf_report_shape(tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.chdir(tmp_path)
    rep = run_perf_harness(iterations=4, report_path=tmp_path / "p.json")
    assert "benchmarks" in rep
    assert len(rep["benchmarks"]) >= 5
    assert Path(rep["report_path"]).is_file()
