# Contributing

This repository tracks RDE behavior changes explicitly. Before opening a PR, verify test boundaries, compatibility expectations, and changelog updates.

## PR checklist

- [ ] Read `docs/63_openayane_rde_testing_policy.md` and keep **RDE classification** checks separate from **Policy action** checks where both appear.
- [ ] If fixtures or golden expectations change, document why the change is intended (not a silent drift).
- [ ] Run local CI parity:
  - `pytest`
  - `openayane-rde schema validate --repo-root .`
  - `openayane-rde golden run --repo-root .`
  - `ruff check src tests`
  - `mypy src`
- [ ] For user-visible behavior changes (CLI flags, schemas, audit action names, config keys, public specs), follow `docs/51_openayane_rde_release_compatibility_policy.md`.
- [ ] Update `CHANGELOG.md` for breaking changes and notable behavior updates.

## Notes

- Benchmark and evaluation outputs are fixture-scoped; do not claim external validity beyond documented scope.
- Keep non-goals and non-claims aligned with `specs/known_limitations.md`.
