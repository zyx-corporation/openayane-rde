# Changelog

## Unreleased

### Changed

- **Breaking:** `evaluate_before_execution()` returns `ExecutionGateEvaluation` (use `.decision` and `.contract`), not a `(ExecutionGateDecision, ExecutionTaskContract)` tuple.
- `RDEResult` includes optional `evaluation_kind`: `pre_synthetic` (tool gate) vs `post_structural` (structural diff / Phase 1 pipeline).
- Phase 1 `run_phase1_evaluation()` sets `evaluation_kind` to `post_structural` on the RDE result when absent, and records it in audit payloads when logging.

### Added

- `execute_after_review_decision()` to resume `SafeExecutionRuntime` after `approve` or `approve_dry_run`.
- `run_phase1_evaluation_from_post_execution_diff()` (`PostExecutionDiff` → Phase 1 evaluation).
- Audit helpers in `openayane_rde.audit.log`: `audit_event_execution_gate_evaluated`, `audit_event_tool_execution`, `audit_event_human_review_requested`, `audit_event_human_review_decided`, `append_audit_event`.
- `ToolExecutionResult.audit_event_id` for correlating SQLite `execution_events` with JSONL audit rows.
- Golden fixture `fixtures/phase3/golden_execution_gate_audit.json`.
- `schemas/rde_result.schema.json`: optional `evaluation_kind` (`pre_synthetic` | `post_structural`).

### Notes

- Phase 1 policy outcome type `ModificationOutcome` (apply / halt / pending review) is distinct from Phase 3 `ToolExecutionResult`; older docs may refer to the former as an execution result — see model docstrings.
