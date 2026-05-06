# required_key_deleted (JSON)

**Scenario:** Preservation contract allows description edits only; a required top-level key (`status`) is removed.

**Corruption type:** Required-field deletion / schema-like integrity break.

**Expected RDE:** `critical_corruption` → `halt`.

**Contract:** `metadata.required_fields` lists keys enforced by `JsonDiff` in golden/benchmark runners.

**Golden lineage:** `tests/golden/fixtures/json_required_key_deleted`.
