# long_text_number_boundary_change (stress / non-claims)

**Scenario:** Long paragraph with a single numeric boundary adjustment inside prose.

**Stress intent (fixture-local):**

- Exercise how the Markdown structural diff extracts **numbers** under long inputs.
- Use a controlled single-number change as an adversarial-ish boundary test.

**Non-claims:**

- This does not claim robustness against arbitrary attacks; it only tests rule-based extraction + policy mapping on this fixture.

**Expected:**

- `classification`: `suspicious_drift` (protected `numbers` changed)
- `required_action`: `human_review`

