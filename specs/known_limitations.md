---
title: "OpenAyane RDE — Known limitations and non-claims"
version: "0.1"
status: "draft"
date: "2026-05-06"
---

# Known limitations and non-claims

This document states what OpenAyane RDE **does not** guarantee. It complements `specs/rde_core_spec.md` and the Phase 6 baseline report (`reports/phase6_baseline_evaluation.md`). Operators, integrators, and reviewers should treat these points as **binding scope boundaries**, not marketing exceptions.

## 1. High assurance and compliance

OpenAyane RDE is **not** a high-assurance safety case, legal compliance engine, or certified audit product.

- No cryptographic integrity guarantees for audit logs or relation stores unless explicitly added and reviewed elsewhere.
- No formal verification of the full Python stack, dependencies, or deployment environment.
- Phase 5 policy positions the project at **Operational Pilot Ready**, not production attestation (`docs/51_openayane_rde_release_compatibility_policy.md`).

## 2. Semantic equivalence

The stack does **not** decide full semantic equivalence of arbitrary natural-language documents or programs.

- Default paths are structural diff, rule-based policy, and optional stub / structural-baseline semantic signals.
- Optional LLM-assisted modes (where present) are **not** treated as ground truth for meaning.
- “Silent ΔM” detection is **conservative and audit-oriented**, not a complete information-flow or program-equivalence analysis.

## 3. Production identity and institution

Institution-bridge models (`openayane_rde.institution`) are **typed skeletons** for accountability boundaries.

- No production proof-of-personhood, enterprise IdP integration, or cryptographic proof of authority is implied.
- `DeterministicInstitutionBridge` is a deterministic mapper for inspection and tests, not organizational workflow software.

## 4. Benchmark and evaluation scope

Phase 6 fixtures under `benchmarks/` are **small, curated, and implementation-aligned**.

- Metrics from `benchmarks/evaluate.py` describe agreement with `expected_rde_result.json` for those fixtures only.
- Counts, rates, and perf samples in `reports/` are **not** estimates of field performance, user studies, or adversarial robustness.
- Long-chain examples include one cumulative-baseline narrative; they do not exhaust multi-session agent behaviours.

## 5. External validity

No claim is made that:

- observed classifications generalize across domains, locales, or model families;
- false-positive / false-negative rates are calibrated for deployment; or
- human-review burden is reduced in real teams (human-in-the-loop economics are **not** benchmarked here).

Any publication or product narrative must separate **repository evidence** (tests, golden files, Phase 6 reports) from **external claims**.

## 6. Maintenance expectation

Changing classifiers, diff engines, or policy defaults may require updating expectations, golden files, and benchmark JSON. That is normal RDE governance, not an indication that limitations above have been “lifted.”

## References

- `specs/rde_core_spec.md`
- `benchmarks/METRICS.md`
- `reports/phase6_baseline_evaluation.md`
- `docs/52_openayane_rde_phase5_completion_report.md` (operational maturity framing)
