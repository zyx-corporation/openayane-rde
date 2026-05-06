# Generator self-report mismatch (benchmarks)

Inventory of **SelfReport vs structural diff** mismatch coverage. `SelfReport` is non-authoritative; evidence is in the diff and RDE classification ([`docs/63_openayane_rde_testing_policy.md`](../../docs/63_openayane_rde_testing_policy.md) §4).

| Location | Role |
|----------|------|
| `silent_delta_claim/` | Benchmark fixture: claims no change while citation and number drift ([`manifest.json`](silent_delta_claim/manifest.json)). |
| `tests/golden/fixtures/self_report_mismatch/` | Golden path: markdown + `self_report.json` → `critical_corruption` / `halt`. |
| `tests/unit/test_phase1_flow.py` | `test_flow_self_report_mismatch_in_audit` — full Phase 1 pipeline + audit payload. |
| `tests/adversarial/test_self_report_mismatch.py` | Markdown and Python cases: citation, number, definition, signature silent changes. |
| `tests/unit/test_python_ast_diff.py` | `test_self_report_function_signature_mismatch` — diff-level mismatch on signatures. |

**Gaps (optional follow-ups):** JSON-domain self-report mismatch golden; mixed-domain long-chain mismatch; non-English prompt fixtures (see Phase 6 completion report §5).
