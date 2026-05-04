# Repository-level convenience Makefile.
#
# The actual paper build logic lives in paper/Makefile so figure paths remain
# local to the LaTeX source directory.
#
# Python: matches CI (.github/workflows/ci.yml): Python 3.11 / 3.12, pytest, ruff, mypy.
# Optional: `make venv PY=/path/to/python3.11` to pin the interpreter.

.PHONY: all paper figures clean distclean check-tools venv dev-install test lint ci

venv:
	@if [ -n "$(PY)" ]; then \
	  "$(PY)" -m venv .venv; \
	elif command -v python3.12 >/dev/null 2>&1; then \
	  python3.12 -m venv .venv; \
	elif command -v python3.11 >/dev/null 2>&1; then \
	  python3.11 -m venv .venv; \
	else \
	  echo "Error: need Python 3.11 or 3.12 on PATH (CI matrix), or set PY=... to a specific interpreter." >&2; \
	  exit 1; \
	fi
	@echo "Created .venv. Next: make dev-install"

dev-install:
	@test -f .venv/bin/python || (echo "Run: make venv first" && exit 1)
	.venv/bin/python -m pip install -U pip
	.venv/bin/pip install -e '.[dev,markdown]'

test:
	@test -f .venv/bin/python || (echo "Run: make venv && make dev-install" && exit 1)
	.venv/bin/python -m pytest

lint:
	@test -f .venv/bin/python || (echo "Run: make venv && make dev-install" && exit 1)
	.venv/bin/ruff check src tests
	.venv/bin/mypy src

# Same order as CI: Tests → Ruff → Mypy
ci: test lint

all: paper

paper:
	$(MAKE) -C paper paper

figures:
	$(MAKE) -C paper figures

check-tools:
	$(MAKE) -C paper check-tools

clean:
	$(MAKE) -C paper clean

distclean:
	$(MAKE) -C paper distclean
