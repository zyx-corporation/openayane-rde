"""Unit tests for PythonAstDiff."""

from __future__ import annotations


from openayane_rde.contract.builder import build_contract
from openayane_rde.core.models import GeneratorOutput, ModelInfo, SelfReport
from openayane_rde.diff.python_ast_diff import PythonAstDiff


def make_contract(**kwargs: object) -> object:
    defaults = dict(
        mode="refactor",
        requested_action="Add error handling.",
        protected_elements=["function_signatures", "imports", "tests", "public_api"],
    )
    defaults.update(kwargs)
    return build_contract(**defaults)  # type: ignore[arg-type]


engine = PythonAstDiff()


def make_go(payload: str, unchanged: list[str] | None = None) -> GeneratorOutput:
    return GeneratorOutput(
        contract_id="tc_test",
        output_type="full_text",
        payload=payload,
        self_report=SelfReport(unchanged_elements=unchanged or []),
        model_info=ModelInfo(provider="mock", model="test"),
    )


# ---------------------------------------------------------------------------
# Function signature change
# ---------------------------------------------------------------------------


def test_function_signature_change_detected() -> None:
    orig = "def process(data: str) -> str:\n    return data\n"
    gen = "def process(data: str, verbose: bool = False) -> str:\n    return data\n"
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    sig_changes = result.signature_changes
    assert len(sig_changes) >= 1
    assert any("process" in str(n.path) for n in sig_changes)


def test_function_signature_protected_change() -> None:
    orig = "def compute(x: int, y: int) -> int:\n    return x + y\n"
    gen = "def compute(x: float) -> float:\n    return x\n"
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    protected = [
        pc for pc in result.protected_element_changes
        if pc.element == "function_signatures"
    ]
    assert len(protected) >= 1


# ---------------------------------------------------------------------------
# Import deletion
# ---------------------------------------------------------------------------


def test_import_deletion_detected() -> None:
    orig = "import os\nimport sys\n\ndef main():\n    pass\n"
    gen = "import sys\n\ndef main():\n    pass\n"
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    deleted = [n for n in result.deleted_nodes if n.kind == "import"]
    assert len(deleted) >= 1
    assert any("os" in str(n.path) for n in deleted)


def test_import_deletion_protected() -> None:
    orig = "import hashlib\n\ndef hash_it(s: str) -> str:\n    return hashlib.md5(s.encode()).hexdigest()\n"
    gen = "def hash_it(s: str) -> str:\n    return s\n"
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    protected = [pc for pc in result.protected_element_changes if pc.element == "imports"]
    assert len(protected) >= 1


# ---------------------------------------------------------------------------
# Public method deletion
# ---------------------------------------------------------------------------


def test_public_method_deletion_detected() -> None:
    orig = "class Service:\n    def run(self) -> None:\n        pass\n    def stop(self) -> None:\n        pass\n"
    gen = "class Service:\n    def run(self) -> None:\n        pass\n"
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    deleted = [n for n in result.deleted_nodes if n.kind == "method"]
    assert any("stop" in str(n.path) for n in deleted)


def test_public_method_protected_change() -> None:
    orig = "class API:\n    def get(self) -> None:\n        pass\n    def post(self) -> None:\n        pass\n"
    gen = "class API:\n    def get(self) -> None:\n        pass\n"
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    protected = [pc for pc in result.protected_element_changes if pc.element == "public_api"]
    assert len(protected) >= 1


# ---------------------------------------------------------------------------
# Test function deletion
# ---------------------------------------------------------------------------


def test_test_function_deletion_detected() -> None:
    orig = "def test_add():\n    assert 1 + 1 == 2\n\ndef test_sub():\n    assert 2 - 1 == 1\n"
    gen = "def test_add():\n    assert 1 + 1 == 2\n"
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    deleted = [n for n in result.deleted_nodes if n.kind == "function"]
    assert any("test_sub" in str(n.before) for n in deleted)


def test_test_function_protected() -> None:
    orig = "def test_security():\n    assert check_auth() is True\n"
    gen = ""
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    protected = [pc for pc in result.protected_element_changes if pc.element == "tests"]
    assert len(protected) >= 1


# ---------------------------------------------------------------------------
# Class deletion
# ---------------------------------------------------------------------------


def test_class_deletion_detected() -> None:
    orig = "class Foo:\n    pass\n\nclass Bar:\n    pass\n"
    gen = "class Foo:\n    pass\n"
    contract = make_contract()
    result = engine.diff(orig, gen, contract)

    deleted = [n for n in result.deleted_nodes if n.kind == "class"]
    assert any("Bar" in str(n.before) for n in deleted)


# ---------------------------------------------------------------------------
# Self-report mismatch
# ---------------------------------------------------------------------------


def test_self_report_function_signature_mismatch() -> None:
    orig = "def run(x: int) -> None:\n    pass\n"
    gen = "def run(x: int, y: int) -> None:\n    pass\n"
    contract = make_contract()
    go = make_go(gen, unchanged=["function signatures"])
    result = engine.diff(orig, gen, contract, generator_output=go)

    mismatches = result.self_report_mismatches
    assert len(mismatches) >= 1


# ---------------------------------------------------------------------------
# No change
# ---------------------------------------------------------------------------


def test_no_change() -> None:
    code = "import os\n\ndef process(x: int) -> int:\n    return x * 2\n"
    contract = make_contract()
    result = engine.diff(code, code, contract)

    assert result.protected_element_changes == []
    assert result.signature_changes == []
    assert result.deleted_nodes == []
