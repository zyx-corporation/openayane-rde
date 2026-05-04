---
title: "OpenAyane RDE Phase 3 評価レポート"
version: "0.2"
date: "2026-05-04"
author: "Tomoyuki Kano"
status: "evaluation report"
---

# OpenAyane RDE Phase 3 評価レポート

## 0. 文書情報

文書名：OpenAyane RDE Phase 3 評価レポート  
対象リポジトリ：`zyx-corporation/openayane-rde`  
対象ブランチ：`phase3`  
評価日：2026-05-04  
最終更新：2026-05-04（ブランチ ahead 数・CI 記述の鮮度修正）  
評価対象：Phase 3 実装一式  
関連文書：

```text
- docs/30_openayane_rde_phase3_specification.md
- docs/31_openayane_rde_phase3_implementation_report.md
- docs/00_development_plan.md
- docs/11_openayane_rde_phase2_spec_2.md
```

## 1. 評価概要

`phase3` ブランチは、`main` より Phase 3 実装・ドキュメントを含む複数コミットが積まれた状態である（**`main` からの ahead 数は base の定義で変わる**ため、固定値は本文に書かない。都度 `git rev-list --count main..phase3` 等で確認すること）。

変更内容は、単なる設計文書の追加ではなく、Agent Execution Gate、SQLiteRelationStore、Safe Execution Runtime、Rollback Manager、Human Review Workflow、Optional Semantic Evaluator、および関連テストを含む実装ブランチである。

現時点での総合評価は以下である。

```text
評価結論：Phase 3 MVP としては成立
成熟度：実装骨格は良好。ただし production-ready ではない
主な強み：契約化 → リスク評価 → Policy → Gate → Runtime / Review / Rollback の最小ループが成立
主な弱点：GitHub Actions 最終確認は PR 単位で残す、PostExecutionRDE未配線、AuditLog統合不足、synthetic RDEの意味の曖昧さ
推奨状態：PR化前に評価レポート・バックログを揃え、**ローカル CI 相当（pytest / ruff / mypy）通過＋Actions green** を完了条件に含めてレビューへ進める
```

Phase 3の実装は、OpenAyane RDEを文書・コード差分評価からAgent実行境界へ拡張するうえで重要な前進である。一方で、現時点の安全性は「保守的に限定されたアプリケーション層制御」であり、完全なsandboxや外部副作用の網羅的制御ではない。

## 2. リポジトリ状況

### 2.1 ブランチ状態

`main` との差分コミット数は **評価時点のスナップショット**であり、レポート本文に固定値を置かない。更新する際はリポジトリで次を実行する。

```bash
git fetch origin
git rev-list --count origin/main..phase3   # phase3 が main より何コミット進んでいるか（例）
git log --oneline origin/main..phase3      # 含まれるコミットの目視
```

```text
repository: zyx-corporation/openayane-rde
branch: phase3
base: main（比較基準は運用に合わせて origin/main 等に置き換え可）
status: 通常 phase3 is ahead of main
PR: 未作成の場合あり
```

**CI（継続的インテグレーション）**

```text
- ローカル（CI と同順序の場合）: pytest / ruff check src tests / mypy src
  本レポート更新時点のワークツリーでは pytest 177 passed を確認済み
- GitHub Actions: ブランチ push / PR 作成後の workflow run を一次情報とし、
  結果 URL または run ID を必要に応じて本節へ追記する
```

### 2.2 主要変更領域

`phase3` ブランチには、以下の主要変更が含まれる。

```text
docs/
  - docs/31_openayane_rde_phase3_implementation_report.md
  - docs/32_openayane_rde_phase3_evaluation_report.md（本書）

schemas/
  - audit_event.schema.json の action enum 拡張

src/openayane_rde/agent/
  - execution_gate.py
  - tool_contract.py

src/openayane_rde/policy/
  - execution_rules.py

src/openayane_rde/relation/
  - sqlite_store.py
  - store.py 拡張

src/openayane_rde/review/
  - workflow.py
  - models.py

src/openayane_rde/runtime/
  - safe_execution.py
  - rollback.py 拡張
  - post_execution.py
  - modification_control.py 調整

src/openayane_rde/semantic/
  - evaluator.py

tests/
  - execution gate
  - tool contract builder
  - sqlite relation store
  - safe execution runtime
  - rollback manager
  - human review workflow
  - optional semantic evaluator
  - integration flow
```

この変更範囲は、Phase 3仕様で定義された実行制御系の中核にほぼ対応している。

## 3. 実装評価

### 3.1 Agent Execution Gate

Agent Execution Gateは、Phase 3の中心機構として成立している。

`evaluate_before_execution()` は、`ToolCallRequest` を受け取り、以下の流れで実行前判断を構成する。

```text
ToolCallRequest
  ↓
build_execution_task_contract
  ↓
score_tool_call_risk
  ↓
synthetic_rde_for_tool
  ↓
relation_store.load_context
  ↓
decide_execution_policy_action
  ↓
ExecutionGateDecision + ExecutionTaskContract
```

評価：良好。

理由は、Agentのtool callを即時実行せず、契約化、リスク分類、RelationContext、Policy判断を通す構造が成立しているためである。これは、OpenAyaneをAgent実行の境界層として位置づけるPhase 3の狙いに合致する。

ただし、API設計には改善余地がある。現在の `evaluate_before_execution()` は `(ExecutionGateDecision, ExecutionTaskContract)` のタプルを返す。これは実装上は便利だが、外部APIとしては不安定になりやすい。

推奨改善：

```text
Option A:
  ExecutionGateEvaluation という集約モデルを導入する

Option B:
  ExecutionGateDecision に contract snapshot を含める

Option C:
  evaluate_before_execution は decision のみ返し、contract repository で参照可能にする
```

短期的には Option A が最も安全である。

### 3.2 Tool call gating

Tool call gatingは、ルールベースMVPとして妥当である。

現実装では、以下のような分類が行われている。

```text
read:
  low risk

write:
  medium risk

delete:
  high risk

execute:
  high or critical

network / external_api:
  high

secret / token / private_key / credential:
  critical
```

危険shell patternとして、`rm -rf /`、`curl | sh`、`wget | sh`、`sudo rm`、`git push --force` などが検出される。

評価：良好。ただし保守的な初期実装。

この分類は、Phase 3の目的である「高リスク実行を自動実行しない」ためには十分に有効である。一方で、shell commandやnetwork requestの意味解析はまだ浅く、現時点では実行を許すよりも止めるための分類器として扱うべきである。

推奨改善：

```text
- command parserを段階的に強化する
- safe command allowlistを導入する
- destructive command denylistをfixture化する
- secret detectionをpath / env / contentの3層へ拡張する
- target_resources推定不能時の説明をReviewRequestへ明示する
```

### 3.3 Safe Execution Runtime

Safe Execution Runtimeは、完全なsandboxではなく、アプリケーション層の限定実行器として実装されている。

主な制御は以下である。

```text
- workspace_root外へのpath escapeをblock
- protected_resources変更をblock
- network_allowed=falseでnetwork/external_apiをblock
- execute actionは実shell実行しない
- dry-run時は副作用を起こさない
- stdout / stderrをmax_output_bytesでtruncate
```

評価：Phase 3 MVPとして妥当。

この実装は安全側に倒れている。特にshell実行を原則実行しない点は、Phase 3の最小実装として正しい。OpenAyaneの安全設計では、初期段階で能力を広げるよりも、実行境界を狭く定義する方が望ましい。

ただし、production運用には不足がある。

```text
- OS-level sandboxではない
- process killを伴う厳密timeoutではない
- memory / CPU / file descriptor limitがない
- symlink attackやTOCTOUへの考慮が不足している可能性がある
- shell/network実行の安全な段階解放設計が未定義
```

推奨改善：

```text
P0:
  symlink / path traversal edge case testを追加する

P1:
  subprocess実行を導入する場合はallowlist方式に限定する

P2:
  container / firejail / nsjail / restricted subprocess profileを検討する
```

### 3.4 SQLiteRelationStore

SQLiteRelationStoreは、Phase 3で最も実装密度が高い箇所である。

以下のテーブルが定義されている。

```text
- relation_records
- drift_patterns
- execution_events
- review_requests
- review_decisions
- rollback_plans
- schema_migrations
```

評価：良好。

RelationStateだけでなく、execution event、review、rollback planを保存できる構造になっており、Phase 3の実行制御履歴を永続化する基盤として成立している。

ただし、いくつか注意点がある。

```text
- SQLiteは単一writer前提であり、複数Agent同時実行には弱い
- metadata_jsonへの依存が大きく、将来migration時の整理が必要
- review_requests tableにproposed_action_summaryなどの仕様項目が不足している可能性がある
- execution_eventsはAuditLogの代替ではなく索引であることを明確に維持すべき
```

推奨改善：

```text
- SQLiteRelationStoreをAuditLogの二次索引として位置づける文書を追加する
- migration v2設計を早めに用意する
- review payloadを欠落なく保存する方式を決める
- write queueまたはtransaction boundaryを明文化する
```

### 3.5 Rollback Manager

Rollback Managerは、`file_snapshot` を中心に最小実装されている。

評価：MVPとして可。

単純なfile writeに対してsnapshotを作成し、復旧する流れはPhase 3の受け入れ基準に対応する。一方で、`git_patch_reverse`、`transactional`、`manual` はまだ十分に実装されたとは見なしにくい。

推奨改善：

```text
P0:
  file_snapshotの複数ファイル対応テストを追加する

P1:
  delete前snapshotとrollbackのE2Eを追加する

P2:
  git_patch_reverseを実装する

P3:
  rollback不可操作の分類とreview理由を強化する
```

### 3.6 Human Review Workflow

Human Review Workflowは、最小構成として成立している。

```text
- human_review decisionからReviewRequestを作成
- pending requestを保持
- ReviewDecisionを投入
- SQLiteRelationStoreへ永続化可能
```

評価：良好。ただしUI/運用には未到達。

Phase 3ではUI非依存APIとして定義されているため、現状のin-memory + optional SQLiteは妥当である。一方で、人間が判断するための情報量、表示順序、承認後のruntime再開フローはまだ薄い。

推奨改善：

```text
- ReviewRequestに判断材料を完全格納する
- approve_dry_runからruntime再開までのE2E testを追加する
- CLIまたはAPI用のreview command設計をPhase 5前倒しで作る
- reviewer_idとauthorityの接続をPhase 4へ引き渡す
```

### 3.7 Optional Semantic Evaluator

Optional Semantic Evaluatorは、rule-based evaluatorとLLM adapter stubとして導入されている。

評価：適切。

Phase 3では、Semantic Evaluatorを中核判断にしないことが重要である。現状は補助評価として留まっており、RDEをLLM evaluatorそのものへ還元しないという設計原則を守っている。

注意点：

```text
- semantic evaluatorのrecommendationをPolicyDecisionへ直結しない
- confidenceを過信しない
- suspected_delta_mをAuditLogに補足情報として保存する
- LLM adapter導入時はprompt / model / response / evaluator versionを監査対象にする
```

### 3.8 既存APIのリネーム（ModificationOutcome）

Phase 3 で **実行結果（ツール実行域）** の `ToolExecutionResult`（仕様上の Post-execution `ExecutionResult` に相当）を導入するにあたり、Phase 1 の **`ExecutionResult`（Policy 駆動の apply / halt / pending の戻り値）** は名称衝突を避けるため **`ModificationOutcome`** にリネームされている（`runtime/modification_control.py` の `apply_or_halt`）。

```text
影響:
  - パッケージ外で旧型名 ExecutionResult を import しているコードは破壊的変更
対応:
  - ModificationOutcome へ置換し、ツール実行結果には ToolExecutionResult を用いる
```

## 4. RDE観点での評価

### 4.1 保存された要素

Phase 3実装は、RDE基本設計の重要要素を保存している。

```text
- RDEは実行器ではなく評価器である
- Policyが実行判断を担う
- TaskContract中心に評価対象を明示する
- RelationStoreを履歴参照として用いる
- AuditLogを一次記録として扱う
- Human Reviewを高リスク判断の逃げ道ではなく制度的判断点として扱う
```

とくに、Agentのtool callを即時実行せず、ExecutionTaskContractへ変換する構造は、RDEの「出力単体ではなく、意図・許可範囲・禁止範囲・履歴との関係で評価する」という思想を保っている。

### 4.2 変換された要素

Phase 1 / Phase 2では、RDEは主に文書・コード差分を評価対象としていた。Phase 3では、評価対象がtool call、外部副作用、workspace mutation、rollback可能性へ拡張されている。

この変換は妥当である。ただし、厳密には以下の違いがある。

```text
StructuralDiff based RDE:
  変更後成果物との差分から意味変化を評価する

Pre-execution Gate:
  実行予定内容と副作用予測からリスクを評価する
```

したがって、Phase 3のpre-execution評価は、RDEそのものというより、RDE思想を使った実行前リスクゲートである。ここを混同しないことが重要である。

### 4.3 補完された要素

Phase 3で補完された要素は以下である。

```text
- ToolCallRequest
- ExecutionTaskContract
- ToolCallRisk
- ExecutionGateDecision
- ToolExecutionResult
- PostExecutionDiff
- RollbackPlan
- ReviewRequest / ReviewDecision
- SQLiteRelationStore
- RuleBasedSemanticEvaluator
```

これらにより、RDEは単発評価から、実行前後の制度的制御ループへ接続可能になった。

### 4.4 未解決の要素

以下は未解決である。

```text
- PostExecutionDiffからRDE Coreへの自動接続
- AuditLogへの統一的execution event append
- 完全なOS sandbox
- shell / network実行の安全な解放戦略
- git_patch_reverse rollback
- Human ReviewのUI / CLI
- ReviewDecisionとauthority / PoP-UIDの接続
- GitHub Actions 上での Phase 3 ブランチ最終確認（ローカル通過後のリモート検証）
- Golden fixtures整備
```

### 4.5 逸脱リスク

Phase 3実装には、以下の逸脱リスクがある。

#### 4.5.1 synthetic RDEの過大評価

`synthetic_rde_for_tool` は、ToolCallRiskから便宜的にRDE分類を作るものである。これはStructuralDiffやSemanticDeltaに基づく本来のRDE分類ではない。

リスク：

```text
- pre-execution risk classificationをRDE本評価と誤認する
- RDEの理論的射程が実装便宜へ縮小される
- 実行前予測と実行後差分評価の区別が失われる
```

対策：

```text
- synthetic RDEを PreExecutionRiskRDE または ToolRiskRDE と明示する
- PostExecutionRDEを別途実装する
- AuditLogに synthetic=true を保存する
```

#### 4.5.2 Rollback可能性を安全性と誤認するリスク

rollback planがあることは、安全であることを意味しない。

不可逆な外部送信、通知、公開、削除、課金、credential漏洩は、rollbackでは回復できない。

対策：

```text
- irreversible=true の場合はrollback_possibleに関係なくhuman_review以上
- external_side_effect=true の場合は原則human_review
- credential accessは常にcritical
```

#### 4.5.3 Human Reviewの形骸化

ReviewRequestに判断材料が不足すると、人間レビューは責任転嫁のボタンになる。

対策：

```text
- expected_side_effects
- forbidden_side_effects
- target_resources
- risk reasons
- rollback strategy
- relation_context
- synthetic_rde / semantic_evaluation
- audit trace
```

をReviewRequestに含める。

#### 4.5.4 SQLiteがAuditLogの代替になるリスク

SQLiteRelationStoreは検索可能な状態・索引であり、不可逆的な一次監査ログではない。

対策：

```text
- AuditLogを一次記録として維持する
- SQLiteにはaudit_event_idを保存する
- AuditLog欠落時のRelationStore更新を制限する
```

## 5. テスト評価

Phase 3では、unit testとintegration testが追加されている。

評価：テスト設計の方向性は良好。

追加済みテスト領域は以下である。

```text
- SQLiteRelationStore
- ToolContractBuilder
- ExecutionGate
- SafeExecutionRuntime
- RollbackManager
- HumanReviewWorkflow
- OptionalSemanticEvaluator
- AgentExecutionGate integration
- ExecutionRollback integration
```

**ローカル**では CI と同様のコマンド（pytest / ruff / mypy）が通過している（本書更新時点で pytest は 177 passed）。**リモート**では GitHub Actions の結果を PR または push 後に確認し、本節に green / 失敗の要約を追記するとよい。

不足しているテストは以下である。

```text
- fixtures/phase3以下のGolden tests
- symlink / path traversal edge cases
- protected resource nested path cases
- approve_dry_runからruntime再開までのE2E
- PostExecutionDiffからRDE評価への接続テスト
- AuditLog JSONL append統合テスト
- rollback失敗時の監査テスト
- external_api / network blocked理由のreview表示テスト
```

## 6. 優先度付き課題

### 6.1 P0：PR前に確認すべき項目

```text
1. pytestを通す（ローカルで確認済みなら PR 説明に記載）
2. ruffを通す
3. mypyを通す
4. schemas/audit_event.schema.json と AuditActionKind の同期を確認する
5. phase3 branchのPRを作成する
6. docs/31とdocs/32の評価内容が矛盾しないか確認する
7. GitHub Actions の workflow run が green であることを確認し、必要なら本レポート §2.1 に追記する
```

### 6.2 P1：Phase 3 MVP完了ラインに必要な項目

```text
1. ExecutionGateEvaluation集約モデルを導入する
2. synthetic RDEであることをモデルまたはmetadataに明示する
3. AuditLog execution helperを追加する
4. PostExecutionDiff → RDE Core の最小接続を追加する
5. Golden fixturesを追加する
6. Human Review approve_dry_run E2Eを追加する
```

### 6.3 P2：Phase 4接続前に必要な項目

```text
1. reviewer_idとauthority modelを接続する
2. irreversible operation taxonomyを整備する
3. protected_resource policyをInstitutionRuleへ接続可能にする
4. SQLite migration v2案を作る
5. AuditLogとSQLiteRelationStoreの責務分離ドキュメントを作る
```

### 6.4 P3：将来拡張

```text
1. shell command allowlist実行
2. network proxy経由実行
3. git_patch_reverse rollback
4. container sandbox integration
5. LLM Semantic Evaluator adapter実装
6. OpenClaw / external agent runtime adapter
```

## 7. 総合評価

Phase 3は、OpenAyane RDEの実装上の重要な節目である。

これまでのOpenAyane RDEは、文書やコードの生成結果に対して「意味変化ΔMが何を保存し、何を変換し、何を歪めたか」を評価する構造だった。Phase 3では、その考え方をAgentのtool callに拡張し、実行前に副作用を契約化し、RelationContextとPolicyを通して実行を制御する構造ができた。

これは、RDEを単なる評価レポート生成器に留めず、Agent実行の制度的境界へ押し出す実装である。

ただし、現時点で完成しているのは「境界の骨格」であり、「運用安全性の完成」ではない。とくに、synthetic RDEの位置づけ、AuditLog統合、PostExecutionRDE、Human Reviewの判断材料、rollbackの網羅性、**GitHub Actions 上の最終確認（PR 単位）**は次の焦点である。

結論として、Phase 3はMVPとして採用可能である。ただし、PRレビュー時には以下の条件を明示するべきである。

```text
- production-readyではない
- full sandboxではない
- synthetic RDEは本来のStructural/Semantic RDEではない
- external side effectは原則human_review以上
- rollbackはfile_snapshot中心の初期実装である
- ローカル CI 相当の通過と GitHub Actions green を完了条件に含める
```

## 8. RDE差異検証

### 8.1 保存された要素

元のPhase 3仕様から保存された要素は以下である。

```text
- Human Review Workflow
- SQLiteRelationStore
- Agent Execution Gate
- Safe Execution Runtime
- Tool call gating
- Rollback Manager
- Optional Semantic Evaluator
- RDE / Policy / Runtime / Review / Rollback の責務分離
- 実行前評価と実行後評価の二段構え
```

### 8.2 変換された要素

仕様では概念上のフローとして記述されていたものが、実装では最小APIとルールベース判定へ変換された。

特に、PreExecution RDEは、構造差分ベースのRDEではなく、ToolCallRiskから合成されるsynthetic RDEへ変換されている。この変換はMVPとしては許容できるが、概念上は明示が必要である。

### 8.3 補完された要素

実装により、以下が補完された。

```text
- ExecutionGateDecisionとExecutionTaskContractの実API
- SQLite schema
- ToolCallRisk scoring
- SafeExecutionRuntimeの限定実行
- RollbackManagerのfile_snapshot
- ReviewWorkflowのin-memory + SQLite永続化
- RuleBasedSemanticEvaluator
- Unit / integration tests
```

### 8.4 未解決のまま残した要素

```text
- 完全なOS sandbox
- shell/network実行
- PostExecutionRDE自動接続
- AuditLog統一ヘルパ
- Golden fixtures
- Human Review UI / CLI
- Institution Layer
- PoP-UID
- cryptographic audit
```

### 8.5 逸脱リスク

主な逸脱リスクは以下である。

```text
- synthetic RDEをRDE本評価と誤認する
- rollback可能性を安全性と混同する
- SQLiteRelationStoreをAuditLogの代替と誤認する
- Human Reviewが形式的承認になる
- 実装上の便宜が理論的主張へすり替わる
```

### 8.6 次回更新方針

次回更新では、以下を実施する。

```text
1. docs/33_openayane_rde_phase3_backlog.md を作成する
2. P0/P1/P2/P3の課題をIssue化またはチェックリスト化する
3. synthetic RDEの位置づけをモデル・文書に反映する
4. AuditLog execution helperの仕様を追加する
5. PostExecutionRDE接続仕様を追加する
6. PRを作成し、GitHub Actions の結果（URL または要約）を評価レポート §2.1 / §5 へ追記する
```
