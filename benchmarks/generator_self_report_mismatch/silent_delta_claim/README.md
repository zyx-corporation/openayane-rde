# silent_delta_claim (self-report mismatch)

**Scenario:** `SelfReport` asserts that numbers, citations, and definitions are unchanged, but the modified document alters a protected numeric target and weakens/removes the primary citation.

**Expected:** `critical_corruption` with structural `self_report_mismatches` and protected-element evidence.

**Golden lineage:** `tests/golden/fixtures/self_report_mismatch` (benchmark-specific `contract_id`).

**Audit completeness:** Downstream relation/audit pipelines should retain mismatch rows; this fixture does not by itself assert log file presence (see Phase 3+ audit tests).
