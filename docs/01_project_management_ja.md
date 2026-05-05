# OpenAyane RDE Project Management Specification 日本語版

この文書は、`zyx-corporation/openayane-rde` における GitHub Projects の推奨設定を定義する。

OpenAyane RDE は、単なるタスクボードとして管理されるべきではない。Project board は、設計意図、実装、レビュー、意味変化監査、マージ判断を接続する開発ガバナンス層として機能すべきである。

## 1. Project identity

推奨 Project 名:

```text
OpenAyane RDE Implementation
```

推奨 description:

```text
Tracks OpenAyane RDE implementation from design intent to executable governance, including relation state, audit log, execution gates, safe runtime, rollback, and semantic evaluation.
```

日本語説明:

```text
OpenAyane RDE の実装を、設計意図から実行可能なガバナンスへ接続して追跡する。対象には、関係状態、監査ログ、実行ゲート、安全実行ランタイム、ロールバック、意味評価を含む。
```

## 2. Core management principle

各実装 item は、元の設計議論から生じる潜在的な意味変化として扱うべきである。

したがって、すべてのタスクは通常の品質基準だけでなく、RDE 的な差異検証によってもレビューされる必要がある。

- preserved: 元の意図または設計要素が保存されている
- authorized transformation: 実装により形式は変化しているが、意図された設計範囲内に収まっている
- inferred extension: 妥当ではあるが、まだ完全には検証されていない拡張が追加されている
- suspicious drift: 元の設計を狭める、誇張する、または別方向へ誘導する可能性がある
- critical distortion: 中核的な設計条件と矛盾する、またはそれを消去している

## 3. Recommended custom fields

| Field | Type | Values / Notes |
|---|---|---|
| Phase | Single select | Phase 0, Phase 1, Phase 2, Phase 3, Phase 4 |
| Component | Single select | Docs, RDE Core, RelationStore, AuditLog, Human Review, Execution Gate, Safe Runtime, Tool Gating, Rollback, Semantic Evaluator, CI, Release |
| Status | Single select | Backlog, Ready, In Progress, In Review, Blocked, Done |
| Priority | Single select | P0, P1, P2, P3 |
| Risk | Single select | Low, Medium, High, Critical |
| RDE Category | Single select | preserved, authorized transformation, inferred extension, suspicious drift, critical distortion |
| Evidence Required | Single select | none, design note, test, audit trace, human review |
| Target Date | Date | 任意の納期またはレビュー予定日 |
| Reviewer | Text or Assignees | 人間レビュアー、または責任を持つレビュアーロール |
| Acceptance Test | Text | 最小限のテスト条件、または受け入れ根拠 |

## 4. Recommended views

### 4.1 Phase Roadmap

目的: 実装全体の進行を表示する。

推奨 layout:

- View type: Roadmap または Table
- Group by: Phase
- Sort by: Priority, Target Date
- Filter: `Status` is not `Done`

### 4.2 Execution Board

目的: 通常の Kanban 実行ボードとして使う。

推奨 layout:

- View type: Board
- Group by: Status
- Filter: すべての active item

### 4.3 Human Review

目的: 明示的な人間判断を必要とするタスクを集約する。

推奨 filter:

```text
Evidence Required:human review OR Risk:High OR Risk:Critical OR RDE Category:suspicious drift OR RDE Category:critical distortion
```

### 4.4 Risk & Drift

目的: マージ前に意味逸脱リスクを特定する。

推奨 layout:

- View type: Table
- Group by: RDE Category
- Sort by: Risk, Priority

### 4.5 Phase 3 Execution Governance

目的: 実行制御層を追跡する。

推奨 filter:

```text
Phase:Phase 3
```

推奨 components:

- Human Review
- SQLiteRelationStore
- Execution Gate
- Safe Runtime
- Tool Gating
- Rollback
- Semantic Evaluator

### 4.6 Documentation

目的: 設計文書と実装文書が乖離しないようにする。

推奨 filter:

```text
Component:Docs
```

## 5. Recommended built-in workflows

利用可能な場合は、以下の GitHub Projects workflow を有効化する。

1. `zyx-corporation/openayane-rde` の Issue と Pull Request を自動追加する。
2. Issue が追加されたら `Status = Ready` に設定する。
3. Pull Request が開かれたら `Status = In Review` に設定する。
4. linked Pull Request が merge されたら `Status = Done` に設定する。
5. 完了済み item は、対応する RDE review checklist が満たされた後にのみ archive する。

## 6. Recommended issue decomposition

初期 issue group:

- Phase 0: project governance and documentation baseline
- Phase 1: RDE core model and difference classification
- Phase 2: persistence, relation state, and audit trace
- Phase 3: execution governance and safety runtime
- Phase 4: integration, evaluation, and release hardening

Phase 3 は以下に分解する。

- Human Review Workflow
- SQLiteRelationStore
- Agent Execution Gate
- Safe Execution Runtime
- Tool call gating
- Rollback Manager
- Optional Semantic Evaluator

## 7. RDE review checklist

非自明な Issue および Pull Request は、以下に答えるべきである。

1. どの元設計要素が保存されたか。
2. 実装上の便宜のために何が変換されたか。
3. 推論された拡張として何が追加されたか。
4. 何が未解決のまま残っているか。
5. 意味逸脱または歪曲のリスクは何か。
6. 次に何をレビューすべきか。

## 8. Pull request gate

以下が満たされるまで、Pull Request は完了扱いにすべきではない。

- Issue または設計文書との明示的な関係を持っている。
- 変更が preserved, authorized transformation, inferred extension, suspicious drift, critical distortion のいずれに該当するかを明示している。
- テスト、またはテストが適用できない理由を含んでいる。
- runtime state に影響する場合、migration または rollback note を含んでいる。
- High または Critical risk の変更では Human review が要求されている。

## 9. Recommended labels

権威ある状態は GitHub Projects fields に置くとしても、repository には以下の labels を推奨する。

```text
phase:0
phase:1
phase:2
phase:3
phase:4
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

OpenAyane RDE において、GitHub Project は制度的インターフェースとして機能すべきである。

Issue = 宣言された意図、または未解決の設計単位。

Pull request = 具体的な意味変化。

Review = RDE による差異検証。

Project field state = その検証に関する制度的記憶。

Merge = codebase への authorized transformation。

## 11. Phase 4: Issue–ブランチ対応と推奨実装順

Phase 4 の各 Issue では、原則として次のブランチ名を用いる。

| Issue | ブランチ名 |
|---|---|
| #27 | `phase4/issue-27-authority-models` |
| #28 | `phase4/issue-28-evidence-decision-models` |
| #29 | `phase4/issue-29-halt-provenance` |
| #30 | `phase4/issue-30-institution-bridge` |
| #31 | `phase4/issue-31-authority-irreversible-tests` |
| #32 | `phase4/issue-32-evidence-handoff-docs` |

推奨実装順（依存とレビュー負荷を踏まえた一つの並び）:

1. #27 Authority models
2. #28 EvidenceHandoff / InstitutionalDecision
3. #29 HaltProvenance
4. #32 Evidence handoff docs
5. #31 Tests for authority / irreversibility
6. #30 Deterministic InstitutionBridge

## 12. RDE 監査上の Pull Request ルール（Phase 4 共通）

- **PR と Issue の対応:** 原則として **1 PR は 1 Issue を close** する。複数 Issue にまたがる変更が不可避な場合は、PR 本文に **primary issue** と **secondary issue** を明記する。
- **PR 本文の構造:** 変更の性質に応じて、少なくとも次の見出しブロックを区別して書く（該当しないブロックは省略可）。
  - `docs-only`
  - `skeleton`
  - `implementation`
  - `hardening`
  - `tests`
- **RDE Notes:** PR 本文に **RDE Notes**（設計意図・差異分類・リスク・レビュー観点）を **必ず** 含める。
- **マージ後:** 対応する Issue に **completion type** をコメントで残す（マージ完了の制度的記録として）。
