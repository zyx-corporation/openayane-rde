"""Python AST structural diff engine for OpenAyane RDE Phase 1.

Detected elements:
  - import changes
  - function signature changes
  - class definition changes
  - public API changes
  - exception handling changes
  - test deletion
"""

from __future__ import annotations

import ast
from collections.abc import Collection
from dataclasses import dataclass, field
from typing import Any

from openayane_rde.core.models import (
    DiffNode,
    GeneratorOutput,
    ProtectedChange,
    SelfReportMismatch,
    StructuralDiff,
    TaskContract,
)
from openayane_rde.diff.base import StructuralDiffEngine


# ---------------------------------------------------------------------------
# AST element extractors
# ---------------------------------------------------------------------------


@dataclass
class _FunctionInfo:
    name: str
    args: list[str]
    defaults: list[Any]
    returns: str | None
    is_method: bool
    class_name: str | None
    lineno: int
    is_test: bool
    has_try_except: bool

    def signature_key(self) -> str:
        if self.class_name:
            return f"{self.class_name}.{self.name}"
        return self.name

    def signature_str(self) -> str:
        args_str = ", ".join(self.args)
        ret = f" -> {self.returns}" if self.returns else ""
        return f"def {self.name}({args_str}){ret}"


@dataclass
class _ClassInfo:
    name: str
    bases: list[str]
    lineno: int
    methods: list[str] = field(default_factory=list)


@dataclass
class _ImportInfo:
    module: str
    names: list[str]
    lineno: int
    is_from: bool

    def key(self) -> str:
        if self.is_from:
            names_str = ", ".join(sorted(self.names))
            return f"from {self.module} import {names_str}"
        return f"import {self.module}"


@dataclass
class _PythonElements:
    functions: dict[str, _FunctionInfo] = field(default_factory=dict)
    classes: dict[str, _ClassInfo] = field(default_factory=dict)
    imports: dict[str, _ImportInfo] = field(default_factory=dict)


def _annotation_str(node: ast.expr | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None


def _arg_str(arg: ast.arg) -> str:
    if arg.annotation is not None:
        return f"{arg.arg}: {_annotation_str(arg.annotation)}"
    return arg.arg


def _extract_elements(source: str) -> _PythonElements:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise ValueError(f"Failed to parse Python source: {exc}") from exc

    elements = _PythonElements()
    _walk_module(tree, elements, class_name=None)
    return elements


def _walk_module(
    node: ast.AST, elements: _PythonElements, class_name: str | None
) -> None:
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
            info = _extract_function(child, class_name)
            elements.functions[info.signature_key()] = info

        elif isinstance(child, ast.ClassDef):
            bases = [_annotation_str(b) or "" for b in child.bases]
            cls_info = _ClassInfo(
                name=child.name, bases=bases, lineno=child.lineno
            )
            for item in ast.iter_child_nodes(child):
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                    fn = _extract_function(item, child.name)
                    elements.functions[fn.signature_key()] = fn
                    cls_info.methods.append(item.name)
            elements.classes[child.name] = cls_info

        elif isinstance(child, ast.Import):
            for alias in child.names:
                key = f"import {alias.name}"
                elements.imports[key] = _ImportInfo(
                    module=alias.name,
                    names=[alias.asname or alias.name],
                    lineno=child.lineno,
                    is_from=False,
                )

        elif isinstance(child, ast.ImportFrom):
            module = child.module or ""
            names = [alias.name for alias in child.names]
            key = f"from {module} import {', '.join(sorted(names))}"
            elements.imports[key] = _ImportInfo(
                module=module,
                names=names,
                lineno=child.lineno,
                is_from=True,
            )


def _extract_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    class_name: str | None,
) -> _FunctionInfo:
    all_args = (
        node.args.posonlyargs
        + node.args.args
        + node.args.kwonlyargs
    )
    if node.args.vararg:
        all_args_strs = [_arg_str(a) for a in all_args]
        all_args_strs.append(f"*{node.args.vararg.arg}")
    else:
        all_args_strs = [_arg_str(a) for a in all_args]
    if node.args.kwarg:
        all_args_strs.append(f"**{node.args.kwarg.arg}")

    defaults = [ast.unparse(d) for d in node.args.defaults]
    returns = _annotation_str(node.returns)

    is_test = node.name.startswith("test_") or node.name.startswith("Test")
    has_try_except = any(isinstance(n, ast.Try) for n in ast.walk(node))

    return _FunctionInfo(
        name=node.name,
        args=all_args_strs,
        defaults=defaults,
        returns=returns,
        is_method=class_name is not None,
        class_name=class_name,
        lineno=node.lineno,
        is_test=is_test,
        has_try_except=has_try_except,
    )


# ---------------------------------------------------------------------------
# PythonAstDiff
# ---------------------------------------------------------------------------


class PythonAstDiff(StructuralDiffEngine):
    """Structural diff engine for Python source files using the standard ast module."""

    domain = "python"

    def diff(
        self,
        original: str,
        generated: str,
        contract: TaskContract,
        generator_output: GeneratorOutput | None = None,
    ) -> StructuralDiff:
        orig = _extract_elements(original)
        gen = _extract_elements(generated)

        protected = set(contract.protected_elements)

        changed_nodes: list[DiffNode] = []
        added_nodes: list[DiffNode] = []
        deleted_nodes: list[DiffNode] = []
        protected_element_changes: list[ProtectedChange] = []
        signature_changes: list[DiffNode] = []
        self_report_mismatches: list[SelfReportMismatch] = []

        # --- Imports ---
        orig_import_keys = set(orig.imports.keys())
        gen_import_keys = set(gen.imports.keys())

        for key in orig_import_keys - gen_import_keys:
            deleted_nodes.append(
                DiffNode(
                    path=f"/imports/{key}",
                    kind="import",
                    before=key,
                    after=None,
                    description=f"Import '{key}' deleted.",
                    risk_hint="high",
                )
            )
            if "imports" in protected:
                protected_element_changes.append(
                    ProtectedChange(
                        element="imports",
                        path=f"/imports/{key}",
                        change_type="deleted",
                        description=f"Protected import '{key}' deleted.",
                        risk_hint="high",
                    )
                )

        for key in gen_import_keys - orig_import_keys:
            added_nodes.append(
                DiffNode(
                    path=f"/imports/{key}",
                    kind="import",
                    before=None,
                    after=key,
                    description=f"Import '{key}' added.",
                    risk_hint="low",
                )
            )

        # --- Functions ---
        orig_fn_keys = set(orig.functions.keys())
        gen_fn_keys = set(gen.functions.keys())

        for key in orig_fn_keys - gen_fn_keys:
            fn = orig.functions[key]
            node_path = f"/functions/{key}"
            deleted_nodes.append(
                DiffNode(
                    path=node_path,
                    kind="function",
                    before=fn.signature_str(),
                    after=None,
                    description=f"Function '{key}' deleted.",
                    risk_hint="high",
                )
            )
            _check_protected_fn_deleted(fn, key, node_path, protected, protected_element_changes)

        for key in gen_fn_keys - orig_fn_keys:
            fn = gen.functions[key]
            added_nodes.append(
                DiffNode(
                    path=f"/functions/{key}",
                    kind="function",
                    before=None,
                    after=fn.signature_str(),
                    description=f"Function '{key}' added.",
                    risk_hint="low",
                )
            )

        for key in orig_fn_keys & gen_fn_keys:
            orig_fn = orig.functions[key]
            gen_fn = gen.functions[key]
            node_path = f"/functions/{key}"

            orig_sig = (orig_fn.args, orig_fn.returns)
            gen_sig = (gen_fn.args, gen_fn.returns)

            if orig_sig != gen_sig:
                sig_node = DiffNode(
                    path=node_path,
                    kind="function_signature",
                    before=orig_fn.signature_str(),
                    after=gen_fn.signature_str(),
                    description=f"Function signature of '{key}' changed.",
                    risk_hint="high",
                )
                changed_nodes.append(sig_node)
                signature_changes.append(sig_node)

                if "function_signatures" in protected:
                    protected_element_changes.append(
                        ProtectedChange(
                            element="function_signatures",
                            path=node_path,
                            change_type="changed",
                            description=f"Protected function signature '{key}' changed.",
                            risk_hint="high",
                        )
                    )

            if orig_fn.has_try_except and not gen_fn.has_try_except:
                changed_nodes.append(
                    DiffNode(
                        path=node_path,
                        kind="exception_handling",
                        before="has try/except",
                        after="no try/except",
                        description=f"Exception handling removed from '{key}'.",
                        risk_hint="high",
                    )
                )

        # --- Classes ---
        orig_cls_keys = set(orig.classes.keys())
        gen_cls_keys = set(gen.classes.keys())

        for key in orig_cls_keys - gen_cls_keys:
            cls = orig.classes[key]
            deleted_nodes.append(
                DiffNode(
                    path=f"/classes/{key}",
                    kind="class",
                    before={"name": cls.name, "bases": cls.bases},
                    after=None,
                    description=f"Class '{key}' deleted.",
                    risk_hint="high",
                )
            )

        for key in gen_cls_keys - orig_cls_keys:
            cls = gen.classes[key]
            added_nodes.append(
                DiffNode(
                    path=f"/classes/{key}",
                    kind="class",
                    before=None,
                    after={"name": cls.name, "bases": cls.bases},
                    description=f"Class '{key}' added.",
                    risk_hint="low",
                )
            )

        for key in orig_cls_keys & gen_cls_keys:
            orig_cls = orig.classes[key]
            gen_cls = gen.classes[key]
            node_path = f"/classes/{key}"

            if sorted(orig_cls.bases) != sorted(gen_cls.bases):
                changed_nodes.append(
                    DiffNode(
                        path=node_path,
                        kind="class_bases",
                        before=orig_cls.bases,
                        after=gen_cls.bases,
                        description=f"Class '{key}' base classes changed.",
                        risk_hint="high",
                    )
                )

            orig_methods = set(orig_cls.methods)
            gen_methods = set(gen_cls.methods)

            for m in orig_methods - gen_methods:
                method_key = f"{key}.{m}"
                if method_key not in gen_fn_keys:
                    deleted_nodes.append(
                        DiffNode(
                            path=f"{node_path}/methods/{m}",
                            kind="method",
                            before=m,
                            after=None,
                            description=f"Method '{key}.{m}' deleted.",
                            risk_hint="high",
                        )
                    )
                    if _is_public(m) and "public_api" in protected:
                        protected_element_changes.append(
                            ProtectedChange(
                                element="public_api",
                                path=f"{node_path}/methods/{m}",
                                change_type="deleted",
                                description=f"Public method '{key}.{m}' deleted.",
                                risk_hint="high",
                            )
                        )

        # --- Self-report mismatch detection ---
        if generator_output is not None:
            self_report_mismatches = _detect_self_report_mismatches(
                generator_output,
                protected_element_changes,
                signature_changes,
                deleted_nodes,
            )

        return StructuralDiff(
            contract_id=contract.contract_id,
            domain="python",
            changed_nodes=changed_nodes,
            added_nodes=added_nodes,
            deleted_nodes=deleted_nodes,
            moved_nodes=[],
            protected_element_changes=protected_element_changes,
            schema_violations=[],
            signature_changes=signature_changes,
            reference_breaks=[],
            self_report_mismatches=self_report_mismatches,
            diff_confidence=0.95,
        )


def _is_public(name: str) -> bool:
    return not name.startswith("_")


def _check_protected_fn_deleted(
    fn: _FunctionInfo,
    key: str,
    node_path: str,
    protected: Collection[str],
    protected_element_changes: list[ProtectedChange],
) -> None:
    if fn.is_test and "tests" in protected:
        protected_element_changes.append(
            ProtectedChange(
                element="tests",
                path=node_path,
                change_type="deleted",
                description=f"Protected test function '{key}' deleted.",
                risk_hint="high",
            )
        )

    if _is_public(fn.name) and not fn.is_method and "public_api" in protected:
        protected_element_changes.append(
            ProtectedChange(
                element="public_api",
                path=node_path,
                change_type="deleted",
                description=f"Public API function '{key}' deleted.",
                risk_hint="high",
            )
        )


def _detect_self_report_mismatches(
    generator_output: GeneratorOutput,
    protected_changes: list[ProtectedChange],
    signature_changes: list[DiffNode],
    deleted_nodes: list[DiffNode],
) -> list[SelfReportMismatch]:
    mismatches: list[SelfReportMismatch] = []
    sr = generator_output.self_report
    unchanged_claimed = {e.lower() for e in sr.unchanged_elements}

    for pc in protected_changes:
        elem = pc.element.lower()
        if elem in unchanged_claimed:
            mismatches.append(
                SelfReportMismatch(
                    reported=f"{pc.element} unchanged",
                    actual=f"{pc.element} {pc.change_type}",
                    description=(
                        f"Generator claimed '{pc.element}' unchanged, "
                        f"but structural diff detected {pc.change_type} at {pc.path}."
                    ),
                    risk_hint="high",
                )
            )

    sr_sig_unchanged = any(
        "signature" in e.lower() or "function" in e.lower()
        for e in sr.unchanged_elements
    )
    if sr_sig_unchanged and signature_changes:
        for sc in signature_changes:
            mismatches.append(
                SelfReportMismatch(
                    reported="function signatures unchanged",
                    actual=f"signature changed at {sc.path}",
                    description=(
                        f"Generator claimed function signatures unchanged, "
                        f"but diff detected change at {sc.path}."
                    ),
                    risk_hint="high",
                )
            )

    return mismatches
