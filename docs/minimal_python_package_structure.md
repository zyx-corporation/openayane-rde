# Minimal Python Package Structure

## 1. Purpose

This document defines the minimal Python package structure for OpenAyane RDE Phase 1.

The package must support:

```text
- core data models
- structural diff plugins
- minimal RDE classifier
- policy bridge
- audit log writer
- golden and adversarial tests
```

Phase 1 prioritizes testability, explicit schemas, and low coupling.

## 2. Recommended Layout

```text
openayane-rde/
  pyproject.toml
  README.md
  LICENSE
  docs/
  schemas/
  src/
    openayane_rde/
      __init__.py
      core/
        __init__.py
        models.py
        ids.py
        errors.py
        time.py
      intent/
        __init__.py
        parser.py
      relation/
        __init__.py
        context_loader.py
        store.py
        update.py
      contract/
        __init__.py
        builder.py
        schema.py
      generator/
        __init__.py
        adapter.py
        mock.py
        prompt_templates.py
      diff/
        __init__.py
        base.py
        markdown_diff.py
        json_diff.py
        python_ast_diff.py
      semantic/
        __init__.py
        delta_engine.py
        stub.py
      rde/
        __init__.py
        core.py
        classifier.py
        scoring.py
      policy/
        __init__.py
        bridge.py
        rules.py
      runtime/
        __init__.py
        modification_control.py
        rollback.py
      audit/
        __init__.py
        log.py
        hash.py
  tests/
    unit/
    golden/
    adversarial/
    long_chain/
```

## 3. Package Boundary

The package name is:

```text
openayane_rde
```

The PyPI distribution name may be:

```text
openayane-rde
```

The Python import should be:

```python
import openayane_rde
```

## 4. pyproject.toml Draft

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "openayane-rde"
version = "0.1.2"
description = "OpenAyane RDE: structural and semantic deviation evaluation for generative and agentic systems"
readme = "README.md"
requires-python = ">=3.12"
license = { text = "MIT" }
authors = [
  { name = "Tomoyuki Kano" }
]
keywords = [
  "rde",
  "openayane",
  "semantic-drift",
  "agent-safety",
  "structural-diff"
]
dependencies = [
  "pydantic>=2.0",
  "jsonschema>=4.0",
  "python-dateutil>=2.8"
]

[project.scripts]
openayane-rde = "openayane_rde.cli.main:main"

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "pytest-cov>=5.0",
  "ruff>=0.4",
  "mypy>=1.8",
  "types-python-dateutil>=2.8",
  "starlette>=0.37",
  "httpx>=0.27"
]
markdown = [
  "markdown-it-py>=3.0"
]
python_ast = []

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.ruff]
line-length = 100
src = ["src", "tests"]

[tool.mypy]
python_version = "3.12"
strict = true
mypy_path = "src"
```

## 5. Core Modules

## 5.1 core/models.py

Purpose:

```text
Define shared Pydantic models or dataclasses.
```

Minimum models:

```text
TaskContract
GeneratorOutput
StructuralDiff
SemanticDelta
RDEResult
PolicyDecision
AuditEvent
RelationContext
ExecutionResult
```

Recommendation:

Use Pydantic v2 for validation and JSON serialization.

## 5.2 core/errors.py

Purpose:

```text
Define explicit exceptions.
```

Minimum errors:

```python
class OpenAyaneError(Exception): ...
class ValidationError(OpenAyaneError): ...
class DiffError(OpenAyaneError): ...
class SemanticDeltaError(OpenAyaneError): ...
class RDEEvaluationError(OpenAyaneError): ...
class PolicyDecisionError(OpenAyaneError): ...
class ExecutionError(OpenAyaneError): ...
class AuditError(OpenAyaneError): ...
```

## 5.3 core/ids.py

Purpose:

```text
Generate stable prefixed IDs.
```

Examples:

```python
new_id("tc")    # tc_xxx
new_id("go")    # go_xxx
new_id("sdiff") # sdiff_xxx
new_id("rde")   # rde_xxx
new_id("audit") # audit_xxx
```

## 6. Diff Modules

## 6.1 diff/base.py

Purpose:

```text
Define common interface for structural diff plugins.
```

Draft interface:

```python
from abc import ABC, abstractmethod

class StructuralDiffEngine(ABC):
    domain: str

    @abstractmethod
    def diff(self, original, generated, contract, generator_output):
        raise NotImplementedError
```

## 6.2 diff/markdown_diff.py

Phase 1 detection:

```text
- headings
- citations
- definitions
- numbers
- links
- code blocks
```

## 6.3 diff/json_diff.py

Phase 1 detection:

```text
- key deletion
- key addition
- type change
- required field deletion
- schema violation
```

## 6.4 diff/python_ast_diff.py

Phase 1 detection:

```text
- function signatures
- imports
- class definitions
- public API
- tests
```

Use Python standard library `ast` first. Tree-sitter can be evaluated later.

## 7. RDE Modules

## 7.1 rde/core.py

Purpose:

```text
Orchestrate RDE evaluation.
```

Draft function:

```python
def evaluate_rde(
    contract,
    generator_output,
    structural_diff,
    semantic_delta,
    relation_context,
):
    ...
```

## 7.2 rde/classifier.py

Purpose:

```text
Classify semantic or structural deviation.
```

Phase 1 classifications:

```text
preserved
authorized_deviation
suspicious_drift
critical_corruption
```

Optional:

```text
benign_incidental_drift
creative_deviation
```

## 7.3 rde/scoring.py

Purpose:

```text
Score preservation, authorization, self-report mismatch, and risk.
```

Initial scoring may be rule-based.

## 8. Policy Modules

## 8.1 policy/bridge.py

Purpose:

```text
Convert RDEResult into PolicyDecision.
```

Initial mapping:

```text
preserved + low risk -> approve
authorized_deviation -> approve_with_notes
suspicious_drift -> human_review
critical_corruption -> halt
```

## 8.2 policy/rules.py

Purpose:

```text
Store configurable policy rules.
```

Phase 1 can hard-code default rules.

## 9. Audit Modules

## 9.1 audit/log.py

Purpose:

```text
Append AuditEvent records to JSONL and read them back.
```

Functions:

```python
def append_event(path, event): ...
def load_events(path): ...
```

## 9.2 audit/hash.py

Purpose:

```text
Compute SHA-256 hash for original and generated states.
```

Function:

```python
def sha256_text(text: str) -> str:
    return "sha256:" + digest
```

## 10. Relation Modules

## 10.1 relation/context_loader.py

Phase 1:

```text
Return neutral RelationContext stub.
```

Example:

```python
RelationContext(
    trust=0.5,
    stability=0.5,
    context_affinity=0.5,
    drift_patterns=[],
)
```

## 10.2 relation/store.py

Phase 1:

```text
Optional in-memory or JSON store.
```

Phase 2:

```text
Persistent relation store.
```

## 11. Generator Modules

## 11.1 generator/adapter.py

Purpose:

```text
Define Generator interface.
```

Phase 1 may not call real LLM APIs.

## 11.2 generator/mock.py

Purpose:

```text
Provide deterministic outputs for tests.
```

## 12. Runtime Modules

## 12.1 runtime/modification_control.py

Phase 1:

```text
No real file modification by default.
Return would-apply / halt / pending-review result.
```

## 12.2 runtime/rollback.py

Phase 1:

```text
Stub only.
```

## 13. Test Layout

```text
tests/unit/
  test_models.py
  test_markdown_diff.py
  test_json_diff.py
  test_python_ast_diff.py
  test_rde_classifier.py
  test_policy_bridge.py
  test_audit_log.py

tests/golden/
  fixtures/
    markdown_preserved/
    markdown_definition_changed/
    markdown_citation_deleted/
    json_required_key_deleted/
    python_signature_changed/

tests/adversarial/
  test_self_report_mismatch.py
  test_silent_number_change.py
  test_deleted_citation.py

tests/long_chain/
  test_long_chain_markdown_drift.py
```

## 14. Minimal CLI Optional

A minimal CLI may be added after models and diff engines are stable.

Example:

```bash
openayane-rde evaluate \
  --contract task_contract.json \
  --original original.md \
  --generated generated.md \
  --domain markdown
```

CLI is not required for the first implementation milestone.

## 15. Development Commands

Recommended setup:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -e '.[dev,markdown]'
pytest
ruff check src tests
mypy src
```

## 16. Implementation Notes

- Prefer pure functions for diff and classifier logic.
- Keep Generator integration optional.
- Keep SemanticDelta stubbed in Phase 1.
- Do not let RDE apply changes.
- Do not update RelationStore without AuditEvent.
- Maintain strict separation between evaluator and mechanism.

```text
RDE:
  evaluate and classify

OpenAyane:
  decide, execute, audit, update history
```
