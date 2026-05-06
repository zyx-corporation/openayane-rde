# OpenAyane RDE — Phase 6 baseline evaluation

## Purpose

This note records a **fixture-local** baseline for the Phase 6 benchmark tree. It does **not** claim external validity, statistical power, or production readiness. Metrics are defined in `benchmarks/METRICS.md` and computed by `benchmarks/evaluate.py`.

## Implementation under test

| Field | Value |
|-------|--------|
| Package version (`pyproject.toml`) | `0.2.0` (M-RDE-G0 pre-gateway API baseline) |
| Git commit evaluated (see JSON `git_commit`) | `9007771977d5ec1f1970925eace59408b8153748` |
| Evaluation harness | `benchmarks/evaluate.py` report version `1` |

The commit above is the **implementation snapshot** used when generating `reports/phase6_baseline_eval.json`. Documentation-only commits after that SHA do not change RDE behaviour until `src/` or benchmark expectations change.

**M-RDE-G0:** Fixture-local benchmark metrics are unchanged at 10/10 agreement; release **0.2.0** adds the stable `POST /v1/evaluate` envelope (`contract_version`, `rde_result` per `schemas/rde_result.schema.json`, `recommended_action`) for gateway integration. See `CHANGELOG.md` [0.2.0] and `specs/known_limitations.md` §8.

## Coverage (this repository state)

| Domain | Evaluation units | Notes |
|--------|------------------|--------|
| `markdown` | 7 | Includes long-chain steps + citation + self-report mismatch + multilingual + long-text boundary |
| `json` | 2 | Required-key deletion + required-key deletion (long payload) |
| `python` | 1 | Signature drift |

**Total units:** 10 (each long-chain step counts as one unit).

## Results summary

| Metric | Value |
|--------|--------|
| Classification agreement | 10 / 10 (100%) |
| Policy action agreement | 10 / 10 (100%) |
| Risk level agreement (where expected JSON specifies `risk_level`) | 8 / 8 (100%) |

**Failures in this run:** none. When a future run disagrees on classification or policy action, `evaluate.py` exits non-zero; this report should be updated to list failing `case_id`s and whether the gap is a **bugfix**, **regression**, or **expectation drift**.

## Latency and performance

| Observation | Value / pointer |
|-------------|-----------------|
| Full `evaluate.py` pass (10 units, local laptop) | ≈ 0.2–0.6 s wall time (order of magnitude; machine-dependent) |
| Phase 5 perf harness | Sample report: `reports/phase6_perf_sample.json` (`openayane-rde perf run --iterations 5 --report …`) |

The perf file uses **low iteration count** (`note: sample_size_low`). Treat numbers as **ordinal / regression hints** on the same hardware, not SLAs. See `docs/51_openayane_rde_release_compatibility_policy.md`.

## Gaps and limitations (explicit)

- **Small N:** Ten units do not span natural language, locales, or adversarial corpora.
- **Expectation coupling:** Agreement is measured against `expected_rde_result.json` authored for this implementation; changing classifiers updates expectations or shows deliberate semantic shifts.
- **No LLM evaluator path** in these fixtures by default.
- **No relation-store or audit persistence checks** inside `evaluate.py` (covered elsewhere in `pytest`).
- **Long-chain mode** here is **cumulative baseline** only (each step vs `original.md`), not step-on-step chaining.

## Artifacts

| File | Role |
|------|------|
| `reports/phase6_baseline_eval.json` | Machine-readable output of `benchmarks/evaluate.py` at baseline time |
| `reports/phase6_perf_sample.json` | Illustrative local perf snapshot (low `iterations`) |

## Regeneration

```bash
python benchmarks/evaluate.py --repo-root . -o reports/phase6_baseline_eval.json
python -m openayane_rde.cli perf run --repo-root . --iterations 40 --report reports/phase6_perf_<date>.json
```

Then edit this markdown if metrics change or failures appear.

## References

- Phase 6 plan: `docs/60_openayane_rde_phase6_issue_branch_plan.md` (P6-7)
- Core vocabulary: `specs/rde_core_spec.md`
