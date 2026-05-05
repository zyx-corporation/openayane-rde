---
title: "OpenAyane RDE Phase 5 Operational Hardening and Ecosystem Integration Specification"
version: "0.2"
date: "2026-05-05"
status: "draft-specification"
---

# OpenAyane RDE Phase 5 Operational Hardening and Ecosystem Integration Specification

## 0. Purpose

Phase 5 turns the Phase 1-4 RDE stack into an operationally usable library/service surface.

Phase 5 does **not** redefine RDE, Policy, Runtime, Human Review, Rollback, or Institution Bridge. It packages and hardens the existing boundaries for real workflows:

```text
local CLI
  -> API/service boundary
  -> adapter integration
  -> configuration
  -> observability
  -> regression suites
  -> release discipline
```

The core question changes from:

```text
Can OpenAyane evaluate and govern a tool action?
```

to:

```text
Can an operator or external agent invoke OpenAyane safely, reproducibly, and audibly under bounded operational assumptions?
```

## 1. Normative references

Read this document together with:

```text
- docs/00_development_plan.md
- docs/37_openayane_rde_phase3_exit_report.md
- docs/40_openayane_rde_phase4_institution_bridge_spec.md
- docs/41_openayane_rde_phase3_to_phase4_evidence_handoff.md
```

Phase 5 depends on the Phase 4 institutional boundary. Institution Bridge remains an authority/accountability layer, not a semantic evaluator.

## 2. Scope

### 2.1 In scope

```text
- CLI entrypoints for local evaluation and operational inspection
- Lightweight service/API boundary
- configuration loader and profile model
- adapter interfaces for filesystem, GitHub PR, and agent runtimes
- operational audit log controls
- relation store selection/configuration
- schema and fixture validation commands
- golden regression suites
- performance measurement harness
- release checklist and compatibility policy
```

### 2.2 Out of scope

```text
- high-assurance OS sandbox
- cryptographic audit log
- full PoP-UID / external identity provider integration
- production web UI
- arbitrary cloud tool execution
- legal/compliance decision engine
- LLM evaluator ensemble as default gate authority
```

These remain L3 or Phase 6+ concerns unless explicitly promoted.

## 3. Phase 5 maturity target

Phase 5 targets **Operational Pilot Ready**, not unrestricted production.

```text
Operational Pilot Ready:
  A developer or bounded internal agent workflow can invoke OpenAyane through a stable CLI/API/adapter interface, with audit trace, configuration, regression tests, and latency measurements.

Not claimed:
  high assurance, legal compliance, cryptographic identity, or full autonomous production execution.
```

## 4. Architectural principle

Phase 5 must preserve the existing separation:

```text
RDE:
  meaning-change and drift evaluation

Policy:
  maps RDE/relation/evidence into operational action

Runtime:
  bounded execution and execution result

Human Review:
  operator decision workflow

Institution Bridge:
  authority / accountability check

Phase 5:
  invocation, configuration, integration, observability, regression, release
```

Phase 5 must not become a new hidden policy layer. If operational defaults affect decisions, they must be represented as explicit configuration or adapter constraints.

## 5. Deliverable groups

Phase 5 should be split into small issues / PRs. Recommended groups:

```text
P5-1: CLI foundation
P5-2: configuration profile loader
P5-3: service/API boundary
P5-4: adapter interfaces
P5-5: GitHub PR review adapter MVP
P5-6: operational audit and relation store controls
P5-7: schema / fixture / golden regression commands
P5-8: performance measurement harness
P5-9: release and compatibility policy
```

## 6. CLI specification

### 6.1 Purpose

The CLI provides local reproducible invocation of the RDE stack.

Initial commands:

```text
openayane-rde evaluate
openayane-rde diff
openayane-rde audit inspect
openayane-rde relation inspect
openayane-rde policy check
openayane-rde institution decide
openayane-rde schema validate
openayane-rde golden run
openayane-rde perf run
```

### 6.2 Command boundaries

#### `evaluate`

Runs a complete evaluation path for a TaskContract + input/output pair or supported fixture.

Minimum inputs:

```text
--contract path/to/contract.json
--before path/to/before
--after path/to/after
--domain markdown|json|python|generic
--audit-log path/to/audit.jsonl
```

Expected output:

```text
- RDEResult summary
- PolicyDecision summary
- audit_event_id references
- machine-readable JSON mode via --json
```

#### `diff`

Runs structural diff only. It must not claim to be full RDE.

#### `audit inspect`

Reads JSONL audit logs and summarizes event chains, missing links, and invalid records.

#### `relation inspect`

Reads configured RelationStore and displays relation context and drift patterns.

#### `policy check`

Runs RDE/Policy mapping without executing runtime actions.

#### `institution decide`

Runs deterministic InstitutionBridge over an EvidenceHandoff and rule/authority fixtures.

#### `schema validate`

Validates model-derived schemas and fixture JSON.

#### `golden run`

Runs golden regression fixtures.

#### `perf run`

Runs latency measurements for core paths.

### 6.3 CLI acceptance criteria

```text
- CLI package entrypoint exists.
- Each command has --help.
- Commands have --json where relevant.
- Commands return non-zero exit code on invalid input.
- Audit-producing commands append or write audit records explicitly.
- No command performs network or external side effects by default.
```

## 7. Configuration specification

### 7.1 Purpose

Configuration makes operational assumptions explicit.

Recommended file:

```text
openayane.toml
```

Initial sections:

```toml
[profile]
name = "local-dev"
mode = "internal-pilot"

[audit]
path = ".openayane/audit.jsonl"
append = true

[relation_store]
backend = "json" # json | sqlite
path = ".openayane/relation.sqlite3"

[runtime]
workspace_root = "."
allow_subprocess_execution = false
max_output_bytes = 64000

[policy]
halt_on_critical_risk = true
allow_auto_execute_low_risk = true

[institution]
rules_path = ".openayane/institution_rules.json"
authority_path = ".openayane/reviewer_authority.json"
```

### 7.2 Config model requirements

```text
- explicit defaults
- environment override policy
- path normalization
- validation errors with actionable messages
- no silent enabling of subprocess/network execution
```

### 7.3 RDE constraint

Config is operational metadata. It must not silently alter RDE classification. If config affects execution or policy action, the effect must be visible in audit or command output.

## 8. Service/API boundary

### 8.1 Purpose

A lightweight API allows external tools and agent runtimes to call OpenAyane without importing Python internals.

Initial API should be optional. CLI and library API remain primary.

### 8.2 Candidate endpoints

```text
POST /v1/evaluate
POST /v1/diff
POST /v1/execution/evaluate-before
POST /v1/institution/decide
GET  /v1/audit/events
GET  /v1/health
```

### 8.3 Service constraints

```text
- local-only by default
- no authentication claim in first MVP unless implemented
- request/response schemas versioned
- audit logging explicit
- no runtime execution endpoint until safety review
```

### 8.4 Non-goal

The service must not become a remote autonomous execution platform in Phase 5 MVP.

## 9. Adapter specification

### 9.1 Adapter interface

Adapters translate external systems into OpenAyane contracts and evidence records.

Recommended protocol:

```python
class OpenAyaneAdapter(Protocol):
    def collect_context(self, source: AdapterSource) -> AdapterContext: ...
    def build_contract(self, context: AdapterContext) -> TaskContract | ExecutionTaskContract: ...
    def produce_evidence(self, result: Any) -> EvidenceHandoff | AuditEvent: ...
```

### 9.2 Initial adapters

```text
FilesystemAdapter:
  local file/path evaluation

GitHubPullRequestAdapter:
  PR diff, changed files, comments, check output

AgentRuntimeAdapter:
  bounded tool call evaluation for external agent runtimes
```

### 9.3 Adapter requirements

```text
- adapters must not bypass TaskContract / ExecutionTaskContract
- adapters must produce auditable evidence
- adapters must declare side-effect profile
- external write operations disabled by default
- adapter-specific missing evidence must be explicit
```

## 10. GitHub PR review adapter MVP

### 10.1 Purpose

The first ecosystem integration target should be GitHub PR review because it is audit-friendly and naturally diff-based.

### 10.2 MVP behavior

```text
Input:
  PR diff or local patch

Output:
  RDE evaluation summary
  risk notes
  protected element changes
  optional Markdown review comment draft
  audit JSONL entry
```

### 10.3 Non-goals

```text
- auto-request-changes by default
- auto-merge
- repository-wide semantic scan
- secret scanning replacement
- legal compliance judgement
```

### 10.4 Acceptance criteria

```text
- Can evaluate a PR diff fixture.
- Can map changed files to TaskContract target scope.
- Can produce review-summary Markdown without posting by default.
- Can write audit event chain.
- Golden PR fixtures are regression-tested.
```

## 11. Operational audit and RelationStore controls

### 11.1 Audit controls

```text
- audit path configured explicitly
- append-only mode by default
- inspect command detects malformed JSONL
- chain completeness check for known event IDs
- redaction policy for sensitive payload fields
```

### 11.2 RelationStore controls

```text
- selectable backend: json | sqlite
- explicit path configuration
- read-only inspect mode
- migration status command
- no implicit production migration
```

### 11.3 Phase 5 constraint

Phase 5 may improve operational controls, but it must not claim cryptographic tamper-proof audit.

## 12. Schema, fixtures, and regression

### 12.1 Schema validation

Commands and CI should validate:

```text
- JSON schemas under schemas/
- fixture JSON under fixtures/
- enum synchronization where schemas are generated or mirrored
- audit event schema compatibility
```

### 12.2 Golden regression

Golden regression should include:

```text
- Markdown drift
- JSON schema corruption
- Python API drift
- Phase 3 execution gate fixture
- Phase 4 institution handoff fixture
- policy halt vs RDE halt fixture
```

### 12.3 Acceptance criteria

```text
- `make ci` or equivalent runs schema + golden checks.
- Golden output changes require explicit fixture update.
- Fixture update PRs include RDE Notes explaining meaning change.
```

## 13. Performance and observability

### 13.1 Performance target

Maintain the low-latency path defined in the development plan.

```text
Core target:
  p50 < 10 ms where feasible for rule-based/cached paths

Measure separately:
  structural diff
  relation lookup
  policy bridge
  institution decision
  audit append
```

Out of core-latency target:

```text
- LLM semantic evaluation
- embedding generation
- full repository scan
- remote API calls
```

### 13.2 Metrics

Initial metrics:

```text
- latency_ms_p50
- latency_ms_p95
- audit_events_written
- schema_validation_failures
- golden_regression_failures
- relation_store_read_latency_ms
- institution_decision_latency_ms
```

### 13.3 Observability output

For Phase 5 MVP, a local JSON report is enough.

```text
.openayane/reports/perf_YYYYMMDD.json
```

## 14. Release and compatibility policy

### 14.1 Versioning

Before any external integration, define compatibility policy for:

```text
- Pydantic models
- JSON schemas
- CLI command flags
- audit event action names
- fixture formats
- config file keys
```

### 14.2 Breaking changes

Breaking changes must be recorded in `CHANGELOG.md`.

Examples:

```text
- renamed public model field
- removed CLI flag
- changed JSON schema required field
- changed audit action enum
- changed default execution policy
```

### 14.3 Release checklist

```text
- pytest passes
- ruff passes
- mypy passes
- schema validation passes
- golden regression passes
- docs link check passes where available
- CHANGELOG updated
- RDE differential note included for semantic behavior changes
```

## 15. Security and safety posture

Phase 5 improves operational safety but does not create high assurance.

Required statements:

```text
- subprocess execution remains disabled by default
- network/external writes disabled by default
- API binds locally by default
- no authentication guarantee unless explicitly implemented
- no cryptographic audit guarantee
- no legal/compliance guarantee
```

If a later PR enables any external side effect by default, it must be treated as a high-risk policy change and require explicit RDE review.

## 16. Recommended Phase 5 Issues

```text
P5-1: Add CLI foundation and command skeletons
P5-2: Add openayane.toml configuration loader
P5-3: Add local-only service/API boundary skeleton
P5-4: Define adapter protocol and filesystem adapter MVP
P5-5: Implement GitHub PR review adapter MVP
P5-6: Add audit inspect and relation inspect operational commands
P5-7: Add schema / fixture / golden regression commands
P5-8: Add performance measurement harness
P5-9: Add release and compatibility policy docs
```

## 17. Issue branch plan and execution order

Phase 5 should use **one Issue = one branch = one PR** as the default. This keeps operational ΔM small and makes it clear which pull request changed which invocation, configuration, adapter, regression, or release surface.

Recommended execution order:

| Order | Issue | Purpose | Branch | Rationale |
|---:|---|---|---|---|
| 1 | #44 / P5-1 | CLI foundation and command skeletons | `phase5/issue-44-cli-foundation` | The CLI is the operator-facing base for config, inspection, regression, and performance commands. |
| 2 | #45 / P5-2 | `openayane.toml` configuration loader | `phase5/issue-45-config-loader` | Configuration fixes safe defaults before adapters or API surfaces consume operational settings. |
| 3 | #49 / P5-6 | audit inspect and relation inspect commands | `phase5/issue-49-audit-relation-inspect` | Early observability makes later Phase 5 changes easier to audit and debug. |
| 4 | #47 / P5-4 | adapter protocol and filesystem adapter MVP | `phase5/issue-47-adapter-filesystem` | Adapter boundaries should be fixed before implementing the GitHub-specific adapter. |
| 5 | #48 / P5-5 | GitHub PR review adapter MVP | `phase5/issue-48-github-pr-adapter` | The GitHub adapter should reuse the generic adapter protocol and remain non-posting by default. |
| 6 | #50 / P5-7 | schema / fixture / golden regression commands | `phase5/issue-50-schema-golden-regression` | Regression should lock behavior after initial CLI and adapter outputs exist. |
| 7 | #53 / P5-8 | performance measurement harness | `phase5/issue-53-performance-harness` | Performance measurement is meaningful after core operational paths are present. |
| 8 | #54 / P5-9 | release and compatibility policy docs | `phase5/issue-54-release-compat-policy` | Release policy should consolidate the operational surfaces introduced earlier. |
| 9 | #46 / P5-3 | local-only service/API boundary skeleton | `phase5/issue-46-local-api-skeleton` | The API should follow CLI/config/adapter stabilization to avoid creating an early remote execution surface. |

The service/API boundary is intentionally placed last even though it is listed as P5-3. A local API created before CLI, config, and adapter defaults are stable can accidentally look like an expanded remote execution surface. Phase 5 should first stabilize local invocation and safe defaults.

### 17.1 PR metadata rule

Every Phase 5 PR should include:

```text
Primary issue: #NN
Completion type:
RDE Notes:
Test plan:
Non-goals preserved:
```

### 17.2 Branching exceptions

Combining issues is allowed only when the combined PR remains a skeleton-only change and the PR body names a primary issue plus secondary issues. The only acceptable early exception is:

```text
phase5/issues-44-45-cli-config-foundation
```

This combines CLI and config foundations. Prefer separate branches unless implementation friction is high.

## 18. Acceptance criteria for Phase 5 exit

Phase 5 can be considered Operational Pilot Ready when:

```text
- CLI can run local evaluation and inspect audit/relation state.
- Config file controls audit, relation store, runtime, policy, and institution paths.
- Service/API skeleton exists or is explicitly deferred.
- At least one adapter MVP exists.
- GitHub PR diff fixture can be evaluated without posting comments by default.
- Schema validation and golden regression run in CI.
- Performance report can be generated locally.
- CHANGELOG / release checklist exists and is used.
- Documentation states all non-goals and safety limits.
```

## 19. RDE differential review

### 19.1 Preserved elements

Phase 5 preserves the separation among RDE, Policy, Runtime, Human Review, Rollback, Institution Bridge, and AuditLog. It also preserves the Phase 4 rule that institutional decision is not semantic evaluation.

### 19.2 Authorized transformations

The internal library stack is transformed into operational surfaces: CLI, config, API, adapters, regression, and performance harness. This is an authorized operational transformation.

### 19.3 Inferred extensions

The following are inferred extensions:

```text
- openayane.toml
- CLI command set
- adapter protocol
- GitHub PR review adapter
- performance report format
- release compatibility policy
- issue-specific branch plan
```

These extend OpenAyane into operational practice without changing the RDE theory.

### 19.4 Unresolved elements

Unresolved elements:

```text
- production authentication
- cryptographic audit
- high-assurance sandbox
- production UI
- external write-side adapters
- legal/compliance integration
```

### 19.5 Drift risks

Key drift risks:

```text
- CLI/API defaults silently alter policy behaviour
- adapter code bypasses TaskContract / ExecutionTaskContract
- API endpoint becomes remote execution surface
- GitHub adapter posts blocking reviews by default
- performance target hides expensive semantic evaluation in core path
- config enables subprocess/network side effects without explicit audit
- multi-issue PRs obscure which Issue introduced which operational ΔM
```

### 19.6 Next update policy

When implementing Phase 5:

```text
- start with CLI/config skeletons
- keep API local-only by default
- implement adapters as evidence producers, not policy bypasses
- require tests before enabling external side effects
- document every default that changes policy or runtime behaviour
- preserve one Issue = one branch = one PR unless explicitly justified
```

## 20. Final statement

Phase 5 is the operationalization layer.

It should make OpenAyane easier to invoke, inspect, configure, integrate, test, and release.

It must not make OpenAyane silently more autonomous, less auditable, or less explicit about institutional responsibility.

## 21. Revision history

| Version | Date | Notes |
|---|---|---|
| 0.1 | 2026-05-05 | Initial Phase 5 operational hardening specification. |
| 0.2 | 2026-05-05 | Added Issue-specific branch plan, execution order, PR metadata rule, and branching exception policy. |
