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

CI (GitHub Actions) runs on **Python 3.11 and 3.12** with: `pip install -e '.[dev,markdown]'`, then `pytest`, `ruff check src tests`, and `mypy src`. Match that locally with the same Python versions.

```bash
# Use 3.11 or 3.12 (same as CI). macOS: brew install python@3.12
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -U pip
pip install -e '.[dev,markdown]'

pytest
ruff check src tests
mypy src
```

From the repository root, **`make venv`** picks `python3.12` or `python3.11` on your PATH (no 3.13 fallback). Then **`make dev-install`**, **`make test`**, and **`make ci`** (full CI parity: pytest + ruff + mypy). Override the interpreter with `make venv PY=/opt/homebrew/bin/python3.11`.

If you see `ModuleNotFoundError: No module named 'pydantic'`, you are not using the venv where dependencies were installed, or you have not run `pip install -e '.[dev,markdown]'` yet.

## Licensing

Paper and documentation are licensed under CC BY 4.0 unless otherwise noted. Code and build scripts are licensed under the MIT License.
