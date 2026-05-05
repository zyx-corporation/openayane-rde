# OpenAyane RDE — Release and compatibility policy (Phase 5)

This document defines how operational surfaces may evolve without silently breaking users or audit semantics. Phase 5 targets **Operational Pilot Ready**, not high assurance, cryptographic audit, or legal compliance.

## Scope

Compatibility expectations cover:

- Pydantic models under `src/openayane_rde/`
- JSON Schemas under `schemas/*.schema.json`
- CLI command names and flags (`openayane-rde` and `python -m openayane_rde.cli`)
- `AuditEvent.action` and related audit vocabulary
- JSON fixtures under `tests/schema_fixtures/`, `tests/golden/fixtures/`, and Phase 5 adapter fixtures
- `openayane.toml` keys documented in `docs/50_openayane_rde_phase5_operational_hardening_spec.md` §7
- Adapter outputs intended for operators (e.g. GitHub PR Markdown drafts, perf JSON reports)

## Breaking change categories

The following are treated as **breaking** for downstream operators, CI, or integrators:

1. **Semantic RDE / policy outcome** — Changes that alter classification, default policy action, or halt semantics for the same structural inputs, unless documented as a deliberate bugfix with RDE review.
2. **Schema incompatibility** — Removing or retyping required JSON Schema fields, or renaming `audit_event` / `task_contract` fields without a migration note.
3. **CLI** — Removing or renaming subcommands, or changing defaults that enable subprocess, network, or external writes.
4. **Config** — Removing or renaming `openayane.toml` keys, or changing defaults that relax safety (e.g. enabling subprocess or network by default).
5. **Audit vocabulary** — Renaming or removing `AuditEvent.action` literals consumed by tooling.
6. **Public adapter contracts** — Changing shapes of operator-facing summaries (e.g. perf report keys, PR adapter bundle fields) without a version bump note.

Non-breaking when done carefully:

- Adding optional fields, new CLI subcommands, new config keys with safe defaults, new audit actions, or new optional API routes (stubs upgrading to implementations).

## Release checklist

Before merging a Phase 5–related change set:

- [ ] `pytest`, `ruff check src tests`, `mypy src` pass (matches CI).
- [ ] `openayane-rde schema validate --repo-root .` passes when schemas or fixtures change.
- [ ] `openayane-rde golden run --repo-root .` passes when RDE/policy/golden paths change.
- [ ] If timings or core paths change materially, run `openayane-rde perf run --repo-root .` and attach or reference the report in the PR.
- [ ] **CHANGELOG.md** updated with a concise operator-facing line.
- [ ] For semantic RDE/policy changes: **RDE differential note** in PR body (preserved / authorized / inferred / risk), per `docs/50` §19.

## CHANGELOG rule

Every user-visible change to CLI, config, default safety posture, schemas, or audit vocabulary should have a **CHANGELOG** entry under an `Unreleased` section (or version section) with:

- What changed (operator-facing wording).
- Whether the change is breaking per the categories above.
- Link to primary issue / PR when applicable.

## Performance and regression expectations

- Performance numbers are **local and environment-dependent**; they are useful for regression on the same machine/CI image, not for absolute SLAs.
- Golden and schema validation commands exist to lock behavior; loosening tests or fixtures to “make CI green” without an RDE note is a governance failure.

## API and authentication

The local HTTP skeleton (`openayane_rde.api`) binds to **local development only** in this phase. There is **no production authentication guarantee** unless explicitly implemented and documented later.

## References

- Phase 5 operational spec: `docs/50_openayane_rde_phase5_operational_hardening_spec.md`
- Project management: `docs/01_project_management.md`
