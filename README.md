# OpenAyane RDE

OpenAyane RDE is a research and implementation repository for OpenAyane, a relational control mechanism built around the RDE (Resonant Deviation Evaluator) evaluation layer.

RDE evaluates semantic change (ΔM) produced by generative or agentic systems. OpenAyane integrates RDE with task contracts, structural diff, semantic delta estimation, policy bridging, safe execution, audit logs, relation-store updates, and historical feedback loops.

## Repository layout

```text
paper/
  openayane_implementation_plan_final_ja.tex
  openayane_implementation_plan_final_ja.pdf
  figures/
    openayane_implementation_flow.svg
    openayane_implementation_flow.png
Makefile
```

## Build

```bash
make figures
make paper
```

`make figures` converts SVG figures into PNG assets. `make paper` builds the Japanese LaTeX paper with XeLaTeX.

## Development (Python package and tests)

CI (GitHub Actions) runs on **Python 3.12** with: `pip install -e '.[dev,markdown]'`, then `pytest`, `ruff check src tests`, and `mypy src`. Match that locally with **Python 3.12 or newer**.

```bash
# Use 3.12+ (same as CI). macOS: brew install python@3.12
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -U pip
pip install -e '.[dev,markdown]'

pytest
ruff check src tests
mypy src
```

From the repository root, **`make venv`** picks `python3.12` or `python3.13` on your PATH. Then **`make dev-install`**, **`make test`**, and **`make ci`** (full CI parity: pytest + `openayane-rde schema validate` + `golden run` + ruff + mypy). Override the interpreter with `make venv PY=/path/to/python3.12`.

If you see `ModuleNotFoundError: No module named 'pydantic'`, you are not using the venv where dependencies were installed, or you have not run `pip install -e '.[dev,markdown]'` yet.

After `pip install -e '.[dev,markdown]'`, CI also runs **`openayane-rde schema validate`** and **`openayane-rde golden run`** (see `.github/workflows/ci.yml`). Locally: `openayane-rde schema validate --repo-root .` and `openayane-rde golden run --repo-root .`.

## Contributing and releases

Use [`CONTRIBUTING.md`](CONTRIBUTING.md) as the primary PR checklist.

- **Tests and RDE vs Policy:** read [`docs/63_openayane_rde_testing_policy.md`](docs/63_openayane_rde_testing_policy.md) before changing golden expectations or classification tests.
- **Compatibility and changelog:** follow [`docs/51_openayane_rde_release_compatibility_policy.md`](docs/51_openayane_rde_release_compatibility_policy.md) and update [`CHANGELOG.md`](CHANGELOG.md) when your PR changes user-visible behavior, CLI, schemas, or public specs.

## Phase 2 scope and limitations

### JSONRelationStore

`JSONRelationStore` is a **Phase 2 minimal** persistence backend: single-file JSON, suitable for development and single-process workflows. It is **not** intended for concurrent production use (no cross-process locking). A **SQLite**-backed store (or equivalent) should be considered for Phase 3 or later when durability and concurrency matter.

### SemanticDelta (`semantic_mode`)

Phase 2 enrichment sets `semantic_mode` to `structural_baseline` while keeping `is_stub=True`. That stack performs **structural-diff-driven semantic candidates** (claims, constraints, safety hints). It does **not** perform full semantic equivalence checking and does **not** use an LLM evaluator by default.

### `allowed_delta_m` / `forbidden_delta_m` matching

Matching uses rule-based substring checks plus a small built-in **synonym map** (`rde/authorization.py`). It is a Phase 2 **baseline**, not domain-specific or language-aware matching. Future directions include locale-aware phrases (e.g. Japanese), code-oriented matchers, and optional LLM-based evaluators in later phases.

## Phase 4 institution models (skeleton)

`openayane_rde.institution` defines **typed skeletons** for `InstitutionRule`, `AuthorityRef`, `ReviewerAuthority`, `EvidenceHandoff`, `InstitutionalDecision`, and `HaltProvenance`, aligned with `docs/40_openayane_rde_phase4_institution_bridge_spec.md`. They establish boundaries for the Institution Bridge only — **not** production authority infrastructure (no PoP-UID, cryptographic proof, or external IdP). Bridge records reference Phase 3 evidence by ID; they are **not** execution results or proofs of authority. `HaltProvenance` keeps policy halt and RDE halt distinguishable in serialized audit payloads.

`DeterministicInstitutionBridge` (`build_handoff` / `decide`) is an MVP, rule-based mapper from `EvidenceHandoff` to `InstitutionalDecision` — inspectable and deterministic, not an LLM.

## Licensing

Paper and documentation are licensed under CC BY 4.0 unless otherwise noted. Code and build scripts are licensed under the MIT License.
