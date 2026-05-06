# OpenAyane RDE — Phase 6 benchmarks

Research-oriented, reproducible fixtures for evaluating RDE behaviour. **`tests/golden/`** remains the original regression suite; **`benchmarks/`** is the Phase 6 tree for reports and metrics. Structural P6-4 cases are also checked by `tests/benchmarks/test_benchmark_p6_structural_fixtures.py` (full `pytest` runs it; skip with `pytest --ignore=tests/benchmarks/`).

## Layout

```text
benchmarks/
  README.md                         ← this file
  markdown_drift/                   ← Markdown structural / drift cases
  json_schema_corruption/           ← JSON shape / required-field cases
  python_api_drift/                 ← Python AST / public API cases
  long_chain_document_corruption/   ← multi-step sequences (P6-5)
  generator_self_report_mismatch/   ← self-report vs diff mismatch (P6-5)
```

## Structural fixtures (P6-4)

| Category | `fixture_id` | Expected `classification` (see `expected_rde_result.json`) |
|----------|--------------|-------------------------------------------------------------|
| `markdown_drift/` | `citation_deleted` | `critical_corruption` |
| `json_schema_corruption/` | `required_key_deleted` | `critical_corruption` |
| `python_api_drift/` | `signature_changed` | `suspicious_drift` |

Each case includes `README.md`, `manifest.json` (golden lineage), and the standard file set below.

Each **fixture** lives in its own directory:

```text
benchmarks/<category>/<fixture_id>/
```

Use **`fixture_id`** = lowercase `snake_case`, stable and unique within the category (e.g. `citation_deleted`, `required_key_removed`).

## Required files per fixture

Align with `tests/golden/test_golden.py` so the same loader patterns can be reused in `benchmarks/evaluate.py` (P6-6):

| File | Purpose |
|------|---------|
| `task_contract.json` | `TaskContract` fields (see `schemas/task_contract.schema.json`). |
| `original.<ext>` | Baseline artifact (`original.md`, `original.json`, `original.py`, …). |
| `modified.<ext>` | Post-change artifact (same extension family as `original`). |
| `expected_rde_result.json` | Expected outcome for benchmark scoring (see below). |
| `self_report.json` | Optional `SelfReport` override for generator self-report mismatch cases. |

Optional:

| File | Purpose |
|------|---------|
| `README.md` | Human notes: intent, threat model, citation to paper/spec section. |
| `manifest.json` | Machine metadata (e.g. `domain`, `tags`, `phase6_issue`). |

## Expected output convention (`expected_rde_result.json`)

Minimum fields used by Phase 6 scoring (extend as needed; CI golden tests may require more):

```json
{
  "classification": "suspicious_drift",
  "risk_level": "high",
  "required_action": "human_review"
}
```

- **`classification`** MUST be a valid `RDEClassification` string (`specs/rde_core_spec.md`).
- **`risk_level`** SHOULD be one of `low` | `medium` | `high` | `critical` when present.
- **`required_action`** SHOULD match `RequiredAction` on `RDEResult` when present.

Stricter assertions (full `RDEResult` shape, policy action) are allowed for individual fixtures but are not required for the skeleton.

## Long-chain fixtures (P6-5)

A long-chain case MAY use either:

- **Sequence directories:** `step_01/`, `step_02/`, … each obeying the single-step file list above, **or**
- **Single directory** with `chain.json` describing ordered paths to child fixture roots (documented when first fixture lands).

Until P6-5 lands, `long_chain_document_corruption/` remains intentionally empty except for this README reference.

## Relationship to CI golden tests

- **`tests/golden/fixtures/`** — regression-locked by `pytest`; keep in sync philosophically with benchmarks when cases overlap.
- **`benchmarks/`** — explicit scope for research reports, metrics, and optional evaluation scripts; failures here do not necessarily fail default CI unless wired in P6-6+.

Copying a case from `tests/golden/fixtures/` into `benchmarks/<category>/` is encouraged for reproducibility; document the source in the fixture `README.md`.

## Non-goals

- **Production load or concurrency** — no throughput SLAs.
- **Full semantic equivalence** — benchmarks assert structural / rule-based RDE behaviour, not NL or arbitrary code equivalence.
- **External validity** — counts and rates apply to these fixtures only unless a report explicitly generalizes (which this repo does not claim by default).
- **Replacing schema validation** — use `openayane-rde schema validate` for JSON Schema drift, not this tree alone.

## References

- Core vocabulary: `specs/rde_core_spec.md`
- Phase 6 plan: `docs/60_openayane_rde_phase6_issue_branch_plan.md` (P6-3–P6-7)
