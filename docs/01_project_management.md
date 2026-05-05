# OpenAyane RDE Project Management Specification

This document defines the recommended GitHub Projects configuration for `zyx-corporation/openayane-rde`.

OpenAyane RDE should not be managed only as a task board. The project board should function as a development governance layer that connects design intent, implementation, review, meaning-change audit, and merge decisions.

## 1. Project identity

Recommended project name:

```text
OpenAyane RDE Implementation
```

Recommended description:

```text
Tracks OpenAyane RDE implementation from design intent to executable governance, including relation state, audit log, execution gates, safe runtime, rollback, and semantic evaluation.
```

## 2. Core management principle

Each implementation item should be treated as a potential meaning change from the original design discussion.

Therefore, every task should be reviewed not only by ordinary quality criteria, but also by RDE-oriented difference inspection:

- preserved: original intent or design element is preserved
- authorized transformation: implementation changes the form but remains within the intended design
- inferred extension: implementation adds a reasonable but not yet fully validated extension
- suspicious drift: implementation may narrow, exaggerate, or redirect the original design
- critical distortion: implementation contradicts or erases a core design condition

## 3. Recommended custom fields

| Field | Type | Values / Notes |
|---|---|---|
| Phase | Single select | Phase 0, Phase 1, Phase 2, Phase 3, Phase 4, Phase 5 |
| Component | Single select | Docs, RDE Core, RelationStore, AuditLog, Human Review, Execution Gate, Safe Runtime, Tool Gating, Rollback, Semantic Evaluator, CI, Release |
| Status | Single select | Backlog, Ready, In Progress, In Review, Blocked, Done |
| Priority | Single select | P0, P1, P2, P3 |
| Risk | Single select | Low, Medium, High, Critical |
| RDE Category | Single select | preserved, authorized transformation, inferred extension, suspicious drift, critical distortion |
| Evidence Required | Single select | none, design note, test, audit trace, human review |
| Target Date | Date | Optional delivery or review date |
| Reviewer | Text or Assignees | Human reviewer or responsible reviewer role |
| Acceptance Test | Text | Minimal test condition or acceptance evidence |

## 4. Recommended views

### 4.1 Phase Roadmap

Purpose: show the overall implementation progression.

Suggested layout:

- View type: Roadmap or Table
- Group by: Phase
- Sort by: Priority, Target Date
- Filter: `Status` is not `Done`

### 4.2 Execution Board

Purpose: ordinary Kanban execution board.

Suggested layout:

- View type: Board
- Group by: Status
- Filter: all active items

### 4.3 Human Review

Purpose: collect tasks that require explicit human judgement.

Suggested filter:

```text
Evidence Required:human review OR Risk:High OR Risk:Critical OR RDE Category:suspicious drift OR RDE Category:critical distortion
```

### 4.4 Risk & Drift

Purpose: identify meaning-drift risk before merge.

Suggested layout:

- View type: Table
- Group by: RDE Category
- Sort by: Risk, Priority

### 4.5 Phase 3 Execution Governance

Purpose: track the execution-control layer.

Suggested filter:

```text
Phase:Phase 3
```

Suggested layout: Board (e.g. the **Phase 3 Execution Governance** view). The filter may be written as `Phase:\"Phase 3\"` in the Project UI/API.

Recommended components:

- Human Review
- SQLiteRelationStore
- Execution Gate
- Safe Runtime
- Tool Gating
- Rollback
- Semantic Evaluator

### 4.6 Documentation

Purpose: ensure design and implementation documents do not drift apart.

Suggested filter:

```text
Component:Docs
```

### 4.7 Phase 4 Institution Bridge

Purpose: track the Phase 4 institutional boundary (Institution Bridge), evidence handoff, and authority / irreversibility models.

Specification: `docs/40_openayane_rde_phase4_institution_bridge_spec.md`

Suggested filter:

```text
Phase:"Phase 4"
```

Suggested layout: Board (**Phase 4 — Institution Bridge** on the org project).

### 4.8 Phase 5 Operational Hardening

Purpose: track the operational layer (CLI, configuration, service/API skeleton, adapters, regression, performance, release policy).

Specification: `docs/50_openayane_rde_phase5_operational_hardening_spec.md`

Suggested filter:

```text
Phase:"Phase 5"
```

Suggested practice: align each issue’s Component and labels with its dominant workload; adapters and API work should explicitly set Evidence Required and Risk.

Suggested layout: Board (**Phase 5 — Operational Hardening** on the org project).

## 5. Recommended built-in workflows

Enable these GitHub Projects workflows where available:

1. Auto-add issues and pull requests from `zyx-corporation/openayane-rde`.
2. Set `Status = Ready` when an issue is added.
3. Set `Status = In Review` when a pull request is opened.
4. Set `Status = Done` when a linked pull request is merged.
5. Archive completed items only after the corresponding RDE review checklist is satisfied.

## 6. Recommended issue decomposition

Initial issue groups:

- Phase 0: project governance and documentation baseline
- Phase 1: RDE core model and difference classification
- Phase 2: persistence, relation state, and audit trace
- Phase 3: execution governance and safety runtime
- Phase 4: integration, evaluation, and release hardening
- Phase 5: operational hardening and ecosystem integration

Phase 3 should be decomposed into:

- Human Review Workflow
- SQLiteRelationStore
- Agent Execution Gate
- Safe Execution Runtime
- Tool call gating
- Rollback Manager
- Optional Semantic Evaluator

## 7. RDE review checklist

Every non-trivial issue and pull request should answer:

1. What original design element is preserved?
2. What was transformed for implementation convenience?
3. What was added as an inferred extension?
4. What remains unresolved?
5. What is the drift or distortion risk?
6. What should be reviewed next?

## 8. Pull request gate

A pull request should not be treated as complete until the following are true:

- It has an explicit relation to an issue or design document.
- It states whether the change is preserved, authorized transformation, inferred extension, suspicious drift, or critical distortion.
- It includes tests or a reason why tests are not applicable.
- It includes migration or rollback notes where runtime state is affected.
- Human review is requested for High or Critical risk changes.

## 9. Recommended labels

These labels are recommended for the repository, even if the authoritative state should live in GitHub Projects fields:

```text
phase:0
phase:1
phase:2
phase:3
phase:4
phase:5
component:docs
component:rde-core
component:relation-store
component:audit-log
component:human-review
component:execution-gate
component:safe-runtime
component:tool-gating
component:rollback
component:semantic-evaluator
risk:low
risk:medium
risk:high
risk:critical
rde:preserved
rde:authorized-transformation
rde:inferred-extension
rde:suspicious-drift
rde:critical-distortion
```

## 10. Operational interpretation

In OpenAyane RDE, a GitHub Project should act as an institutional interface.

Issue = declared intention or unresolved design unit.

Pull request = concrete meaning change.

Review = RDE difference inspection.

Project field state = institutional memory of that inspection.

Merge = authorized transformation into the codebase.

## 11. Phase 5: Issue-branch mapping and recommended order

Tracked on GitHub; matches `docs/50_openayane_rde_phase5_operational_hardening_spec.md` §16.

| Issue | Branch name |
|---|---|
| [#44](https://github.com/zyx-corporation/openayane-rde/issues/44) | `phase5/issue-44-cli-foundation-skeletons` |
| [#45](https://github.com/zyx-corporation/openayane-rde/issues/45) | `phase5/issue-45-openayane-toml-config` |
| [#46](https://github.com/zyx-corporation/openayane-rde/issues/46) | `phase5/issue-46-local-service-api-skeleton` |
| [#47](https://github.com/zyx-corporation/openayane-rde/issues/47) | `phase5/issue-47-adapter-protocol-fs-mvp` |
| [#48](https://github.com/zyx-corporation/openayane-rde/issues/48) | `phase5/issue-48-github-pr-adapter-mvp` |
| [#49](https://github.com/zyx-corporation/openayane-rde/issues/49) | `phase5/issue-49-audit-relation-inspect-commands` |
| [#50](https://github.com/zyx-corporation/openayane-rde/issues/50) | `phase5/issue-50-schema-fixture-golden-regression-cmds` |
| [#53](https://github.com/zyx-corporation/openayane-rde/issues/53) | `phase5/issue-53-performance-measurement-harness` |
| [#54](https://github.com/zyx-corporation/openayane-rde/issues/54) | `phase5/issue-54-release-compatibility-policy-docs` |

Recommended implementation order:

1. #44 CLI foundation
2. #45 `openayane.toml` loader
3. #46 Local-only service/API skeleton
4. #47 Adapter protocol + filesystem MVP
5. #48 GitHub PR review adapter MVP
6. #49 Audit/relation inspect commands
7. #50 Schema/fixture/golden regression commands
8. #53 Performance measurement harness
9. #54 Release and compatibility policy docs

To onboard these onto the GitHub Project (recommended name OpenAyane RDE Implementation), add each issue manually and set **Phase = Phase 5**. Workflows from §5 that auto-add issues do not backfill historical issues.

With `gh` authenticated (`gh auth refresh -s read:project -s project`) and the project configured with a **Phase** single-select including **Phase 5**, run `scripts/add_phase5_issues_to_github_project.sh` to add any missing issues and set the Phase field in one step.
