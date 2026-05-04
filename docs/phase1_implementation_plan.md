# Phase 1 Implementation Plan

## 1. Purpose

Phase 1 implements the Structural RDE MVP.

The goal is not complete semantic understanding. The goal is to build the minimal OpenAyane mechanism that can:

```text
- accept an explicit TaskContract,
- accept or produce a GeneratorOutput,
- run StructuralDiff for Markdown, JSON, and Python,
- detect protected element changes,
- detect Generator self_report mismatch,
- classify changes with a minimal RDE Core,
- produce PolicyDecision,
- record AuditEvent,
- halt critical corruption before applying changes.
```

## 2. Scope

### 2.1 In Scope

```text
Data models:
  - TaskContract
  - GeneratorOutput
  - StructuralDiff
  - RDEResult
  - PolicyDecision
  - AuditEvent

Diff engines:
  - MarkdownDiff
  - JsonDiff
  - PythonAstDiff

Core logic:
  - protected element detection
  - self_report mismatch detection
  - minimal RDE classifier
  - minimal PolicyBridge
  - AuditLog JSONL writer

Tests:
  - unit tests
  - golden tests
  - adversarial tests
```

### 2.2 Out of Scope

```text
- full Semantic Delta Engine
- LLM evaluator ensemble
- full RelationStore update algorithm
- real tool execution
- sandbox runtime
- OpenClaw integration
- Institution Layer
- PoP-UID integration
- cryptographic audit log
```

## 3. Milestones

## 3.1 Milestone 1: Repository and Package Skeleton

Deliverables:

```text
pyproject.toml
src/openayane_rde/__init__.py
src/openayane_rde/core/models.py
src/openayane_rde/core/errors.py
src/openayane_rde/core/ids.py
tests/unit/
```

Acceptance criteria:

```text
- package can be installed in editable mode
- pytest can run
- base models can be imported
```

## 3.2 Milestone 2: Data Models

Deliverables:

```text
TaskContract model
GeneratorOutput model
StructuralDiff model
RDEResult model
PolicyDecision model
AuditEvent model
```

Acceptance criteria:

```text
- models validate required fields
- invalid enum values are rejected
- timestamp fields are generated or validated
- JSON serialization works
```

## 3.3 Milestone 3: Markdown Structural Diff

Deliverables:

```text
src/openayane_rde/diff/markdown_diff.py
```

Detected elements:

```text
- headings
- paragraphs
- definitions
- citations
- links
- code blocks
- numbers
- dates
```

Acceptance criteria:

```text
- heading deletion detected
- citation deletion detected
- definition change detected
- number change detected
- protected element changes reported
```

## 3.4 Milestone 4: JSON Structural Diff

Deliverables:

```text
src/openayane_rde/diff/json_diff.py
```

Detected elements:

```text
- key deletion
- key addition
- value change
- type change
- required field deletion
- schema violation if schema is provided
```

Acceptance criteria:

```text
- deleted required key is detected
- type change is detected
- protected schema key change is detected
```

## 3.5 Milestone 5: Python AST Structural Diff

Deliverables:

```text
src/openayane_rde/diff/python_ast_diff.py
```

Detected elements:

```text
- import change
- function signature change
- class definition change
- public API change
- exception handling change
- test deletion
```

Acceptance criteria:

```text
- function signature mutation detected
- import deletion detected
- public method deletion detected
- test function deletion detected
```

## 3.6 Milestone 6: RDE Minimal Classifier

Deliverables:

```text
src/openayane_rde/rde/classifier.py
src/openayane_rde/rde/core.py
```

Minimum classifications:

```text
preserved
authorized_deviation
suspicious_drift
critical_corruption
```

Acceptance criteria:

```text
- no protected change -> preserved or authorized_deviation
- allowed change -> authorized_deviation
- protected change outside allowed_delta_m -> suspicious_drift
- critical protected change -> critical_corruption
- self_report mismatch raises risk
```

## 3.7 Milestone 7: Policy Bridge

Deliverables:

```text
src/openayane_rde/policy/bridge.py
src/openayane_rde/policy/rules.py
```

Initial mapping:

```text
preserved + low risk -> approve
authorized_deviation -> approve_with_notes
suspicious_drift -> human_review
critical_corruption -> halt
```

Acceptance criteria:

```text
- RDEResult converted into PolicyDecision
- critical_corruption never auto-applies
- suspicious_drift requires human review or revision
```

## 3.8 Milestone 8: AuditLog JSONL

Deliverables:

```text
src/openayane_rde/audit/log.py
```

Acceptance criteria:

```text
- AuditEvent is appended to JSONL
- event can be loaded back
- hash_before and hash_after can be stored
- RDEResult and PolicyDecision IDs are recorded
```

## 3.9 Milestone 9: Golden and Adversarial Tests

Deliverables:

```text
tests/golden/
tests/adversarial/
```

Acceptance criteria:

```text
- markdown definition change fixture passes
- markdown citation deletion fixture passes
- json required key deletion fixture passes
- python function signature change fixture passes
- generator self_report mismatch fixture passes
```

## 4. Implementation Order

Recommended order:

```text
1. package skeleton
2. core models
3. audit event model and JSONL writer
4. structural diff base class
5. MarkdownDiff
6. JsonDiff
7. PythonAstDiff
8. RDE classifier
9. PolicyBridge
10. golden tests
11. adversarial tests
```

Reasoning:

```text
- models stabilize the interface first
- audit early prevents untraceable evaluation
- MarkdownDiff gives fastest validation path
- JSON and Python add structural rigor
- RDE classifier should be built after diff outputs stabilize
```

## 5. Minimal Runtime Flow

Phase 1 runtime flow:

```python
def run_phase1_evaluation(original, generated_output, task_contract):
    structural_diff = run_structural_diff(original, generated_output, task_contract)
    semantic_delta = semantic_delta_stub(structural_diff)
    rde_result = evaluate_rde(task_contract, structural_diff, semantic_delta, generated_output)
    policy_decision = decide_policy(rde_result, task_contract)
    audit_event = write_audit_event(
        task_contract=task_contract,
        generator_output=generated_output,
        structural_diff=structural_diff,
        rde_result=rde_result,
        policy_decision=policy_decision,
    )
    return policy_decision
```

Phase 1 does not need to apply file patches by default. It may stop at evaluation and decision.

## 6. Test Strategy

### 6.1 Unit Tests

```text
tests/unit/test_models.py
tests/unit/test_markdown_diff.py
tests/unit/test_json_diff.py
tests/unit/test_python_ast_diff.py
tests/unit/test_rde_classifier.py
tests/unit/test_policy_bridge.py
tests/unit/test_audit_log.py
```

### 6.2 Golden Tests

Golden tests should use fixed fixtures.

```text
tests/golden/fixtures/markdown_preserved/
tests/golden/fixtures/markdown_definition_changed/
tests/golden/fixtures/json_required_key_deleted/
tests/golden/fixtures/python_signature_changed/
```

Each fixture should include:

```text
original
modified
task_contract.json
expected_rde_result.json
```

### 6.3 Adversarial Tests

Adversarial tests should include:

```text
- self_report says citations unchanged but citation removed
- self_report says numbers unchanged but number changed
- generated output changes function signature silently
- generated output removes required JSON field
```

## 7. Success Criteria

Phase 1 is complete when:

```text
- all core models validate
- Markdown, JSON, and Python structural diffs run
- protected element changes are detected
- generator self-report mismatches are detected
- RDE returns minimal classifications
- PolicyBridge halts critical corruption
- AuditLog records all evaluation steps
- golden tests pass
- adversarial tests pass for critical cases
```

## 8. Known Limitations

Phase 1 does not prove semantic safety.

It provides a structural foundation for RDE evaluation.

Known limitations:

```text
- semantic equivalence is approximate or stubbed
- relation update is minimal
- no real tool execution
- no institution layer
- no calibrated thresholds
```

## 9. Next Phase Entry Conditions

Phase 2 may begin when:

```text
- Phase 1 golden tests are stable
- structural diff output schema is stable
- audit logs are available for relation update experiments
- protected element detection has acceptable recall on test corpus
```

Phase 2 should introduce:

```text
- SemanticDeltaEngine
- RelationStore minimal update
- trust/stability/context_affinity provisional formulas
- long-chain edit tests
```
