# signature_changed (Python)

**Scenario:** Refactor contract allows adding error handling but forbids signature changes; `process_data` loses default argument and changes behaviour.

**Corruption type:** Function signature / public API drift.

**Expected RDE:** `suspicious_drift` → `human_review`; `risk_level` is `medium` under the current classifier (see `expected_rde_result.json`).

**Golden lineage:** `tests/golden/fixtures/python_signature_changed`.
