# Tests

Normative guidance for **what tests should fix** (RDE classification vs Policy action, golden meaning, self-report non-authority): [`docs/63_openayane_rde_testing_policy.md`](../docs/63_openayane_rde_testing_policy.md).

- **`tests/golden/`** — Contract-style expectations in `expected_rde_result.json`; asserts should separate **classification** (RDE) from **required_action** / policy where both are checked.
- **`tests/unit/test_policy_bridge.py`** — Policy mapping only (synthetic `RDEResult` inputs).
- **`tests/unit/test_rde_classifier.py`** / **`tests/adversarial/`** — RDE-side behavior; adversarial cases include self-report vs diff mismatch ([`docs/63`](../docs/63_openayane_rde_testing_policy.md) §4).

Self-report mismatch coverage inventory: [`benchmarks/generator_self_report_mismatch/README.md`](../benchmarks/generator_self_report_mismatch/README.md).
