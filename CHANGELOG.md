# Changelog

## Unreleased

### Changed

- **Breaking:** `evaluate_before_execution()` returns `ExecutionGateEvaluation` (use `.decision` and `.contract`), not a `(ExecutionGateDecision, ExecutionTaskContract)` tuple.
- `RDEResult` includes `evaluation_kind`: `pre_synthetic` (tool gate) vs `post_structural` (structural diff / Phase 1 pipeline).
- `RDEResult` includes `evidence_basis` (`EvidenceBasis` のリスト): 合成ゲートは `tool_risk_rule` / `execution_contract`、Phase 1／実行後パイプラインは `structural_diff` / `semantic_delta`（`PostExecutionDiff` に副次影響列があれば `observed_side_effects`）。`schemas/rde_result.schema.json` を同期。
- Phase 1 `run_phase1_evaluation()` sets `evaluation_kind` and `evidence_basis` on the RDE result, and records them in audit payloads when logging.
- `SafeExecutionRuntime` now supports allowlisted subprocess execution with effective timeout (`subprocess.run(..., timeout=...)`), returning `timed_out` when the process is terminated by timeout.
- `ExecutionTaskContract` now includes `external_side_effect_kind` and `allowed_network_domains`; tool risk scoring and gate policy use the taxonomy (`read_only_fetch`, `state_changing_request`, `payment_or_billing`, `data_exfiltration_risk`, etc.).

### Added

- Phase 6 P6-10 / P6-9 / P6-8: `docs/62_openayane_rde_phase6_completion_report.md`, `specs/known_limitations.md`, `papers/openayane_rde_paper_draft.md` (technical report skeleton).
- Phase 6 P6-7: `reports/phase6_baseline_evaluation.md`, `reports/phase6_baseline_eval.json`, and sample `reports/phase6_perf_sample.json` (low-iteration perf harness) for fixture-local baseline documentation.
- Phase 6 P6-6: `benchmarks/evaluate.py` (JSON benchmark report, fixture discovery, classification/action/risk metrics), `benchmarks/METRICS.md`, and `tests/benchmarks/test_benchmark_evaluate_smoke.py`.
- Phase 6 P6-5: `benchmarks/long_chain_document_corruption/safety_framework_cumulative` (three-step cumulative baseline drift) and `benchmarks/generator_self_report_mismatch/silent_delta_claim`; tests `tests/benchmarks/test_benchmark_p6_long_chain.py`, `test_benchmark_p6_self_report_mismatch.py`.
- Phase 6 P6-4 structural benchmark fixtures under `benchmarks/markdown_drift/citation_deleted`, `benchmarks/json_schema_corruption/required_key_deleted`, `benchmarks/python_api_drift/signature_changed` (aligned with golden cases; benchmark-specific `contract_id`s).
- `tests/benchmarks/test_benchmark_p6_structural_fixtures.py` — optional CI skip via `pytest --ignore=tests/benchmarks/`.
- Phase 6 `benchmarks/` skeleton: category directories, `benchmarks/README.md` (fixture layout, naming, `expected_rde_result.json` convention, non-goals).
- Phase 6 public documentation: `specs/rde_core_spec.md` (RDE core terms and non-claims) and schema prose (`specs/task_contract_schema.md`, `specs/rde_result_schema.md`, `specs/audit_event_schema.md`, `specs/relation_store_schema.md`) aligned with `schemas/*.schema.json` and `openayane_rde.core.models`.
- `execute_after_review_decision()` to resume `SafeExecutionRuntime` after `approve` or `approve_dry_run`.
- `run_phase1_evaluation_from_post_execution_diff()` (`PostExecutionDiff` → Phase 1 evaluation).
- Audit helpers in `openayane_rde.audit.log`: `audit_event_execution_gate_evaluated`, `audit_event_tool_execution`, `audit_event_human_review_requested`, `audit_event_human_review_decided`, `append_audit_event`.
- `ToolExecutionResult.audit_event_id` for correlating SQLite `execution_events` with JSONL audit rows.
- Golden fixture `fixtures/phase3/golden_execution_gate_audit.json`.
- `SQLiteRelationStore.applied_schema_versions()` — applied rows in `schema_migrations` (for migration tests / ops).
- `docs/36_openayane_rde_sqlite_migration_v2_plan.md` — review payload persistence migration plan (GitHub Issue D1).

### Notes

- Phase 1 policy outcome type `ModificationOutcome` (apply / halt / pending review) is distinct from Phase 3 `ToolExecutionResult`; older docs may refer to the former as an execution result — see model docstrings.
