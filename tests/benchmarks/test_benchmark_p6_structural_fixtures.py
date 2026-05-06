"""Lock Phase 6 structural benchmark fixtures to current RDE + policy behaviour.

These tests reuse the golden runner so benchmark cases stay aligned with
`tests/golden/test_golden.py` semantics. Default CI includes this module; exclude with::

    pytest --ignore=tests/benchmarks/
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tests.golden import test_golden as golden

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = REPO_ROOT / "benchmarks"

_CASES: list[tuple[Path, str, str, str, Any]] = [
    (
        BENCHMARK / "markdown_drift" / "citation_deleted",
        "markdown",
        "original.md",
        "modified.md",
        None,
    ),
    (
        BENCHMARK / "json_schema_corruption" / "required_key_deleted",
        "json",
        "original.json",
        "modified.json",
        "use_contract_metadata",
    ),
    (
        BENCHMARK / "python_api_drift" / "signature_changed",
        "python",
        "original.py",
        "modified.py",
        None,
    ),
]


@pytest.mark.parametrize(
    "fixture_dir,domain,orig,mod,json_fields_mode",
    _CASES,
    ids=[p[0].name for p in _CASES],
)
def test_p6_structural_benchmark_matches_expected(
    fixture_dir: Path,
    domain: str,
    orig: str,
    mod: str,
    json_fields_mode: Any,
) -> None:
    assert fixture_dir.is_dir(), f"missing fixture dir: {fixture_dir}"
    expected = golden.load_expected(fixture_dir)
    required: list[str] | None = None
    if json_fields_mode == "use_contract_metadata":
        contract = golden.load_contract(fixture_dir)
        required = contract.metadata.get("required_fields", [])
    classification, action = golden.run_golden_fixture(
        fixture_dir, domain, orig, mod, required_json_fields=required
    )
    assert classification == expected["classification"], (
        f"{fixture_dir}: expected classification {expected['classification']!r}, got {classification!r}"
    )
    assert action == expected["required_action"], (
        f"{fixture_dir}: expected policy action {expected['required_action']!r}, got {action!r}"
    )
