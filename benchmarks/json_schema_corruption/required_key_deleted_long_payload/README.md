# required_key_deleted_long_payload (stress / adversarial-ish)

**Scenario:** A required top-level key (`status`) is deleted while the JSON payload contains a longer description string.

**Stress intent (fixture-local):**

- Keep the corruption signal simple (`required_field_deleted`) but include a longer payload to verify stable detection.
- Validate that the benchmark harness remains reproducible with larger text blobs.

**Policy/limitations alignment:**

- This fixture is aligned with `specs/known_limitations.md` non-claims: it does not demonstrate adversarial robustness in the wild.

**Expected:**

- `classification`: `critical_corruption`
- `risk_level`: `critical`
- `required_action`: `halt`

