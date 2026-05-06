---
title: "Phase 6+ benchmark expansion plan"
version: "0.1"
status: "planning"
date: "2026-05-06"
---

# Benchmark expansion plan (multilingual, domain, adversarial)

This document **plans** benchmark growth for GitHub [#94](https://github.com/zyx-corporation/openayane-rde/issues/94). It does **not** implement new fixtures or change `evaluate.py` detection rules. Implementation should follow separate issues so claims stay aligned with [`specs/known_limitations.md`](../specs/known_limitations.md).

## 1. How `benchmarks/evaluate.py` discovers work

| Mechanism | Behaviour |
|-----------|-----------|
| Directory walk | One benchmark **category** = top-level directory under `benchmarks/` (e.g. `markdown_drift/`). |
| Single fixture | Subdirectory with `task_contract.json` and `original.*` / `modified.*` (no `chain.json`) → one evaluation **unit**. |
| Long chain | Subdirectory with `chain.json` listing `steps`; each step is a subdirectory with its own `modified.*` and `expected_rde_result.json`. |
| Domains | Inferred from `original.md`, `original.json`, or `original.py` → `MarkdownDiff`, `JsonDiff`, or `PythonAstDiff`. |
| Scoring | Compares actual `RDEResult.classification` and policy `required_action` to `expected_rde_result.json`; optional `risk_level`. |

New categories must follow the same layout so discovery stays automatic.

## 2. Planned category: multilingual (Markdown-first)

| Aspect | Plan |
|--------|------|
| Intent | Curated non-English (or mixed-locale) **Markdown** pairs where structural drift (headings, lists, citations) mirrors English fixtures. |
| `evaluate.py` mapping | Same as existing `markdown_drift`: domain `markdown`, single or long-chain layout. |
| Rule / engine gap | `MarkdownDiff` is not locale-aware; **semantic** nuance in translation is out of scope until explicitly modeled. Expectations must be expressed via structural edits (`expected_rde_result.json`), not “meaning in language L”. |
| Limitations | Update [`specs/known_limitations.md`](../specs/known_limitations.md) §4 when adding each batch: fixtures remain small and curated; no claim of cross-lingual robustness. |

## 3. Planned category: additional domains

| Aspect | Plan |
|--------|------|
| Intent | New artefact families (e.g. additional structured text, config formats) **only** after `DiffDomain` and a diff engine are defined in code. |
| `evaluate.py` mapping | Today only `markdown` / `json` / `python` are supported in `_detect_domain_and_files`. New domains require extending that function and the diff branch in `_run_rde` / `_run_unit`. |
| Rule gap | Without a new engine, fixtures cannot be scored; plan work as **schema + engine + fixtures + tests** in one milestone. |

## 4. Planned category: adversarial and near-boundary

| Aspect | Plan |
|--------|------|
| Intent | Minimal edits that sit near policy thresholds (e.g. benign vs suspicious drift) to stress **classification stability**, not to imply optimal ROC. |
| `evaluate.py` mapping | Same discovery as structural fixtures; expectations are golden JSON only. |
| Rule gap | May expose coarse thresholds in `evaluate_rde` / policy rules; document any expectation change as **benchmark intent**, not as tuned production policy. |
| Limitations | Explicitly mark in `known_limitations`: adversarial coverage is synthetic and narrow; not a substitute for red-team or field evaluation. |

## 5. Follow-up issues (suggested)

1. **Per-locale or per-domain batch** — one issue per batch with acceptance: fixtures + `tests/benchmarks/` + `METRICS.md` / report updates if needed.
2. **Engine extension** — separate issue when adding a `DiffDomain`.
3. **Paper / external claims** — only after claims are bound to new evidence; align with [`papers/openayane_rde_paper_draft.md`](../papers/openayane_rde_paper_draft.md) and `known_limitations`.

## 6. References

- [`benchmarks/README.md`](README.md), [`benchmarks/METRICS.md`](METRICS.md)
- [`docs/00_development_plan.md`](../docs/00_development_plan.md) §9.6 (track **7B**)
