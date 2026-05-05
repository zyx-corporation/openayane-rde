"""Measure core local paths; emit JSON report (no network, no semantic/LLM)."""

from __future__ import annotations

import json
import math
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from openayane_rde.audit.log import append_event
from openayane_rde.contract.builder import build_contract
from openayane_rde.core.models import AuditEvent, GeneratorOutput, ModelInfo, RelationStoreRecord, SelfReport
from openayane_rde.diff.markdown_diff import MarkdownDiff
from openayane_rde.policy.bridge import decide_policy
from openayane_rde.relation.store import JSONRelationStore
from openayane_rde.runtime._flow import run_structural_diff
from openayane_rde.rde.core import evaluate_rde
from openayane_rde.semantic.stub import semantic_delta_stub


def _percentile_ms(samples_s: list[float], q: float) -> float | None:
    if not samples_s:
        return None
    s = sorted(samples_s)
    n = len(s)
    idx = min(n - 1, max(0, math.ceil(q * n) - 1))
    return s[idx] * 1000.0


def _bench(name: str, fn: Callable[[], object], iterations: int) -> dict[str, Any]:
    samples: list[float] = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        fn()
        samples.append(time.perf_counter() - t0)
    return {
        "name": name,
        "category": "core_local",
        "iterations": iterations,
        "p50_ms": _percentile_ms(samples, 0.50),
        "p95_ms": _percentile_ms(samples, 0.95),
        "note": None if iterations >= 10 else "sample_size_low",
    }


def run_perf_harness(
    *,
    iterations: int = 40,
    report_path: Path | None = None,
) -> dict[str, Any]:
    """Run micro-benchmarks and write ``report_path`` (default under ``.openayane/reports``)."""

    contract = build_contract(mode="preservation", requested_action="perf", protected_elements=["claims"])
    md_before = "# T\n\n[cite](http://x) 1.\n"
    md_after = "# T\n\n[cite](http://x) 2.\n"
    go = GeneratorOutput(
        contract_id=contract.contract_id,
        output_type="full_text",
        payload=md_after,
        self_report=SelfReport(),
        model_info=ModelInfo(provider="local", model="perf"),
    )

    def structural_diff_loop() -> None:
        run_structural_diff(md_before, go, contract, "markdown")

    engine = MarkdownDiff()

    def markdown_engine_loop() -> None:
        engine.diff(md_before, md_after, contract, go)

    store_path = Path(".openayane") / "_perf_relation.json"
    store = JSONRelationStore(store_path)
    rec = RelationStoreRecord(subject_id="p1", object_id="d1")
    store.upsert(rec)

    def relation_lookup_loop() -> None:
        store.load_context("p1", "d1")

    rde_go = GeneratorOutput(
        contract_id=contract.contract_id,
        output_type="full_text",
        payload=md_before,
        self_report=SelfReport(),
        model_info=ModelInfo(provider="local", model="perf-rde"),
    )
    sd = run_structural_diff(md_before, rde_go, contract, "markdown")
    sem = semantic_delta_stub(sd, contract)
    rde_result = evaluate_rde(
        contract=contract,
        generator_output=rde_go,
        structural_diff=sd,
        semantic_delta=sem,
    )

    def policy_bridge_loop() -> None:
        decide_policy(rde_result, contract)

    audit_file = Path(".openayane") / "_perf_audit.jsonl"

    def audit_append_loop() -> None:
        append_event(
            audit_file,
            AuditEvent(actor="system", action="evaluate_rde", explanation="perf harness"),
        )

    benches = [
        _bench("structural_diff_markdown", structural_diff_loop, iterations),
        _bench("markdown_diff_engine", markdown_engine_loop, iterations),
        _bench("relation_json_load_context", relation_lookup_loop, iterations),
        _bench("policy_decide", policy_bridge_loop, iterations),
        _bench("audit_append_jsonl", audit_append_loop, max(5, iterations // 4)),
    ]

    report: dict[str, Any] = {
        "generated_at_utc": datetime.now(tz=UTC).isoformat(),
        "environment_note": "Local, single-machine timings; not comparable across hardware.",
        "remote_or_llm_paths": "excluded_by_design",
        "benchmarks": benches,
    }

    out = report_path
    if out is None:
        stamp = datetime.now(tz=UTC).strftime("%Y%m%d")
        out = Path(".openayane") / "reports" / f"perf_{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    report["report_path"] = str(out.resolve())
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
