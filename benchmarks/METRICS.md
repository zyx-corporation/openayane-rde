# Phase 6 benchmark metrics

This document defines metrics computed by `benchmarks/evaluate.py`. All rates are **fixture-local**: they describe agreement between the **current OpenAyane RDE implementation** and the **documented expectations** in each case’s `expected_rde_result.json`, not performance on a real-world population.

## Inputs

| Source | Role |
|--------|------|
| `benchmarks/**/expected_rde_result.json` | Declared `classification`, `required_action`, optional `risk_level`. |
| RDE + policy pipeline | Actual `RDEResult.classification`, `PolicyDecision.action`, `RDEResult.risk_level`. |

## Primary metrics

### Classification agreement

- **Definition:** fraction of evaluation units where `actual_classification == expected_classification`.
- **Mapping:** `expected_rde_result.json` → field `classification` (must be a valid `RDEClassification` per `specs/rde_core_spec.md`).

### Policy action agreement

- **Definition:** fraction of units where the policy layer’s `action` equals `expected_rde_result.required_action`.
- **Note:** This measures end-to-end consistency with the golden/benchmark convention (RDE → `decide_policy`), not organizational policy in production.

### Risk level agreement (optional)

- **Definition:** when `expected_rde_result.json` includes `risk_level`, fraction of those units where `actual_risk_level` matches.
- **Units with no `risk_level` in expected** are excluded from the denominator (`risk_level_scored_cases` in the JSON report).

## Secondary breakdowns

- **`by_domain`:** `markdown` | `json` | `python` — counts and classification matches per domain.
- **Long-chain:** each `step_NN` is a separate evaluation unit (cumulative-baseline comparison).

## Non-claims

- **No confidence intervals** and no hypothesis tests.
- **No implied recall/precision** for “critical corruption” or “suspicious drift” in the wild; labels here are fixture-defined.
- **No audit-log completeness metric** in v1 of `evaluate.py` (see Phase 3+ tests for audit persistence).

## Report shape

See `benchmarks/evaluate.py` output: top-level `metrics` object and per-case `cases` array with boolean `classification_match`, `action_match`, and optional `risk_match`.
