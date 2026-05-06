---
title: "OpenAyane RDE 全体実装計画"
version: "0.1-draft"
date: "2026-05-04"
author: "Tomoyuki Kano"
status: "development plan"
---

# OpenAyane RDE 全体実装計画

## 0. 文書の目的

本書は、OpenAyane RDEの基本設計に基づき、リポジトリ全体の実装計画をPhase単位で整理する開発ロードマップである。

既存の基本設計文書では、OpenAyaneをRDE（Resonant Deviation Evaluator）中心の意味変化監査機構として定義した。OpenAyaneは、Generatorの出力、文書編集、コード変更、ツール実行、関係履歴更新を、単なる品質評価ではなく、元の意図・構造・制約からの意味変化ΔMとして扱う。

本計画では、その思想を実装可能な工程へ分解する。目的は、個別機能の羅列ではなく、OpenAyaneが「生成系の意味変化を観測し、分類し、制御し、履歴へ戻す機構」として段階的に成立するための道筋を示すことである。

## 1. 基本設計から導かれる実装原則

### 1.1 GeneratorとEvaluatorを分離する

Generatorは変換案を生成する主体であり、最終判断者ではない。RDEは、Generatorの自己申告ではなく、TaskContract、StructuralDiff、SemanticDelta、RelationState、Policyを照合して、生成結果の意味変化を評価する。

この原則により、実装では次を守る。

```text
- GeneratorOutput.self_report は補助情報として扱う
- 実際の差分は StructuralDiff / SemanticDelta から抽出する
- RDE分類は Generator の説明ではなく差分と契約に基づく
- PolicyDecision は RDEResult と履歴・制度条件に基づく
```

### 1.2 変換をTaskContractとして明示する

RDEは、出力単体を評価しない。評価対象は、元状態、生成後状態、許可された変換、禁止された変換、保護対象、関係履歴の組である。

したがって、すべての評価フローはTaskContractを中心に組み立てる。

```text
TaskContract
  - mode
  - target_scope
  - requested_action
  - allowed_delta_m
  - forbidden_delta_m
  - protected_elements
  - review_policy
```

### 1.3 Structural DiffをRDEの構造化レンズにする

RDEはDiffそのものではない。しかし、RDEが意味変化を評価するためには、構造差分が必要である。

Phase 1では、Markdown、JSON、Python ASTを対象にStructuralDiffを安定させる。これは、後続PhaseにおけるSemanticDelta、RelationStore、Policy補正の基盤になる。

### 1.4 Semantic ΔMを段階的に導入する

完全な意味理解をPhase 1で目指さない。Phase 1ではSemanticDeltaをstubまたは構造由来の簡易候補とし、Phase 2で構造差分由来の意味候補抽出へ拡張する。

LLM evaluator ensembleは有用だが、初期実装の中核にはしない。RDEをLLM評価器そのものに還元しないためである。

### 1.5 RelationStoreは評価結果の履歴化である

RelationStoreは単なる記憶ではない。過去のRDE分類、PolicyDecision、AuditEvent、drift patternを集約し、次回以降のreview threshold、risk adjustment、context_affinityに反映するための状態である。

Phase 2以降では、Phase1EvaluationResultを標準入力単位としてRelationStoreを更新する。

### 1.6 PolicyはRDEの外側に置く

RDEは意味変化を評価し、逸脱分類と推奨アクションを返す。Policyは、その評価結果を実行判断へ変換する。

```text
RDE:
  preserved / authorized_deviation / suspicious_drift / critical_corruption などを分類する

Policy:
  approve / approve_with_notes / request_revision / human_review / halt / rollback を決める
```

この分離により、評価ロジックと実行統制を混同しない。

## 2. 全体Phase構成

OpenAyane RDEの実装は、以下のPhaseに分割する。

```text
Phase 0: Concept Freeze and Repository Baseline
Phase 1: Structural RDE MVP
Phase 2: Semantic ΔM and Relation Feedback
Phase 3: Agent Execution Gate
Phase 4: Institution and Accountability Layer
Phase 5: Operational Hardening and Ecosystem Integration
Phase 6: Research Evaluation and Public Specification
```

Phase 3 出口（L1 境界の固定）および Phase 4 Institution Bridge 初期仕様: [`37_openayane_rde_phase3_exit_report.md`](37_openayane_rde_phase3_exit_report.md)、[`40_openayane_rde_phase4_institution_bridge_spec.md`](40_openayane_rde_phase4_institution_bridge_spec.md)、[`41_openayane_rde_phase3_to_phase4_evidence_handoff.md`](41_openayane_rde_phase3_to_phase4_evidence_handoff.md)。**Phase 4 実装完了の総括（出口記録）:** [`43_openayane_rde_phase4_completion_report.md`](43_openayane_rde_phase4_completion_report.md)。

Phase 5（運用化・CLI / 設定 / アダプタ / 回帰など）の詳細・Issue 分割・**推奨実行順**: [`50_openayane_rde_phase5_operational_hardening_spec.md`](50_openayane_rde_phase5_operational_hardening_spec.md)（GitHub [#44](https://github.com/zyx-corporation/openayane-rde/issues/44) 〜 [#54](https://github.com/zyx-corporation/openayane-rde/issues/54)）。着手は同文書 §17 に従い、通常 **#44（CLI）を最初**とする。

Phase 6（研究評価・公開仕様）の実行計画: [`60_openayane_rde_phase6_issue_branch_plan.md`](60_openayane_rde_phase6_issue_branch_plan.md)。**Phase 6 完了の出口記録:** [`62_openayane_rde_phase6_completion_report.md`](62_openayane_rde_phase6_completion_report.md)。

各Phaseは、前Phaseの成果物を明確に入力として受け取る。特にPhase 1で生成されるPhase1EvaluationResultは、Phase 2以降の中核的な接続点となる。

## 3. Phase 0: Concept Freeze and Repository Baseline

### 3.1 目的

Phase 0の目的は、RDEをOpenAyaneの中心概念として固定し、リポジトリ内の文書・モデル・用語・ディレクトリ構成を揃えることである。

この段階では、機能実装よりも「何を作るのか」「何を作らないのか」を明確にする。

### 3.2 実装対象

```text
docs/00_development_plan.md
  - 本書

docs/02_openayane_basic_design.md
  - OpenAyane基本設計

docs/03_openayane_rde_verification_report.md
  - RDE視点での設計検証

docs/minimal_python_package_structure.md
  - Python package構成方針

pyproject.toml
src/openayane_rde/
tests/
```

### 3.3 完了条件

```text
- RDEの定義が明文化されている
- RDEがDiff、Policy、Safety Filter、LLM Evaluatorそのものではないと明示されている
- TaskContract、GeneratorOutput、StructuralDiff、SemanticDelta、RDEResult、PolicyDecision、AuditEventの関係が整理されている
- Phase 1以降の実装順序が定義されている
- リポジトリがPython packageとしてテスト可能な最小構成を持つ
```

### 3.4 逸脱リスク

Phase 0での最大のリスクは、RDEを抽象思想として広げすぎ、実装単位へ落ちないことである。対策として、以降のすべてのPhaseで受け入れ基準とテスト対象を明示する。

## 4. Phase 1: Structural RDE MVP

### 4.1 目的

Phase 1は、Structural RDE MVPを実装する段階である。

完全な意味理解ではなく、最小限のOpenAyane機構として、次を実現する。

```text
- 明示的なTaskContractを受け取る
- GeneratorOutputを受け取る
- Markdown / JSON / PythonのStructuralDiffを実行する
- protected_elementsの変更を検出する
- Generator self_reportと実差分の不一致を検出する
- 最小RDE分類を返す
- PolicyDecisionへ変換する
- AuditEventを記録する
- critical_corruptionを自動適用前に停止する
```

### 4.2 主要成果物

```text
src/openayane_rde/core/models.py
  - TaskContract
  - GeneratorOutput
  - StructuralDiff
  - SemanticDelta stub
  - RDEResult
  - PolicyDecision
  - AuditEvent
  - Phase1EvaluationResult

src/openayane_rde/diff/
  - structural_base.py
  - markdown_diff.py
  - json_diff.py
  - python_ast_diff.py

src/openayane_rde/rde/
  - classifier.py
  - core.py

src/openayane_rde/policy/
  - bridge.py
  - rules.py

src/openayane_rde/audit/
  - log.py

tests/unit/
tests/golden/
tests/adversarial/
```

### 4.3 実装順序

```text
1. core models
2. schema export and validation
3. AuditEvent model and JSONL writer
4. StructuralDiff base interface
5. MarkdownDiff
6. JsonDiff
7. PythonAstDiff
8. SemanticDelta stub
9. RDE minimal classifier
10. PolicyBridge
11. Phase1EvaluationResult aggregation
12. golden tests
13. adversarial tests
14. CI integration
```

### 4.4 テスト方針

Phase 1では、構造的破壊の検出を重視する。

```text
Markdown:
  - heading deletion
  - citation deletion
  - definition shift
  - number change
  - protected section modification

JSON:
  - required key deletion
  - type change
  - schema violation
  - protected key mutation

Python:
  - function signature change
  - import deletion
  - public API deletion
  - test deletion
  - exception handling change

Generator self_report:
  - citation unchangedと主張しながら引用を削除
  - number unchangedと主張しながら数値を変更
  - function signature unchangedと主張しながら変更
```

### 4.5 完了条件

```text
- Phase1EvaluationResultを返せる
- Markdown / JSON / PythonのStructuralDiffが動作する
- protected_elementsの変更を検出できる
- self_report mismatchを検出できる
- RDEが preserved / authorized_deviation / suspicious_drift / critical_corruption を返せる
- PolicyBridgeがcritical_corruptionをhaltへ変換できる
- AuditLogにTaskContract、Diff、RDE、PolicyDecisionを記録できる
- unit / golden / adversarial testsがCIで通る
```

### 4.6 Phase 2への接続条件

```text
- Phase1EvaluationResultのschemaが安定している
- structural_diff output schemaが安定している
- audit_eventがRelationStore更新根拠として使える
- SemanticDelta stubがPhase 2で拡張可能な形になっている
```

## 5. Phase 2: Semantic ΔM and Relation Feedback

### 5.1 目的

Phase 2は、OpenAyaneを単発の構造評価器から、履歴を持つ意味変化監査機構へ拡張する段階である。

Phase 1の出力であるPhase1EvaluationResultを標準入力単位とし、RelationStore、RelationContext Loader、履歴ベースのrisk adjustment、SemanticDeltaEngine Phase 2を実装する。

### 5.2 主要成果物

```text
src/openayane_rde/relation/store.py
  - JSONRelationStore
  - load / save / get / upsert

src/openayane_rde/relation/update.py
  - update_relation_from_evaluation_result
  - update_drift_patterns
  - update_generator_reliability_profile
  - update_document_fragility_profile

src/openayane_rde/relation/context_loader.py
  - neutral stubからRelationStore参照へ拡張

src/openayane_rde/rde/authorization.py
  - allowed_delta_m matching

src/openayane_rde/rde/scoring.py
  - history-aware risk scoring

src/openayane_rde/semantic/delta_engine.py
  - StructuralDiff由来のSemanticDelta候補抽出

src/openayane_rde/policy/bridge.py
  - relation_contextに基づくpolicy adjustment

tests/long_chain/
  - markdown long-chain drift tests
```

### 5.3 RelationStore Minimal

Phase 2では、まずJSONベースのRelationStoreを実装する。SQLite化は後続でよい。

```text
.relation_store/relation_state.json
```

最小保存対象は以下とする。

```text
- subject_id
- object_id
- trust
- stability
- context_affinity
- interaction_count
- critical_corruption_count
- suspicious_drift_count
- self_report_mismatch_count
- drift_patterns
- generator_reliability_profile
- document_fragility_profile
- review_threshold_adjustment
- last_delta_m
- last_audit_event_id
```

### 5.4 Relation Update

Phase 2では、厳密な数理モデルよりも、監査可能な保守的ルールを優先する。

```text
preserved:
  trust +0.01
  stability +0.01

authorized_deviation:
  trust +0.005
  stability +0.005 or unchanged

suspicious_drift:
  trust -0.03
  stability -0.02
  suspicious_drift_count +1
  review_threshold_adjustment +0.05

critical_corruption:
  trust -0.10
  stability -0.05
  critical_corruption_count +1
  review_threshold_adjustment +0.15

self_report_mismatch:
  trust -0.05
  self_report_mismatch_count +1
  drift_patterns add/update self_report_mismatch
```

すべてのスコアは `0.0 <= x <= 1.0` にclipする。

### 5.5 SemanticDeltaEngine Phase 2

Phase 2のSemanticDeltaは、LLMによる完全意味評価ではなく、StructuralDiff由来の意味候補抽出から始める。

```text
Markdown:
  definition diff -> changed_definitions
  number diff -> changed_numbers
  citation/link deletion -> changed_references
  protected heading deletion -> changed_claims

JSON:
  required field deletion -> changed_constraints
  type change -> changed_constraints
  schema violation -> changed_safety_conditions

Python:
  function signature change -> changed_constraints
  public API deletion -> changed_constraints
  test deletion -> changed_safety_conditions
  exception handling removal -> changed_safety_conditions
```

### 5.6 allowed_delta_m matching

Phase 1では、allowed_delta_mが存在すればauthorized_deviationへ寄りやすい。Phase 2では、実際の差分内容とallowed_delta_m / forbidden_delta_mを照合する。

```text
allowed_delta_m = ["sentence restructuring"]
actual = number changed
=> authorized_deviationにしない

allowed_delta_m = ["error handling"]
actual = try/except added
=> authorized_deviation候補

forbidden_delta_m = ["function signature change"]
actual = function signature changed
=> suspicious_driftまたはcritical_corruption
```

### 5.7 完了条件

```text
- Phase1EvaluationResultからRelationStoreを更新できる
- AuditEventがある評価のみRelationStore更新対象にできる
- RelationContext LoaderがRelationStoreから実データを返せる
- PolicyBridgeが履歴に基づくrisk adjustmentを行える
- allowed_delta_m matchingが実装されている
- SemanticDeltaEngineが構造差分由来の意味候補を抽出できる
- long-chain drift testで20回以上の編集連鎖を扱える
- 同種driftが複数回出た場合にdrift_patternsへ蓄積される
- document_fragility_scoreまたはreview_threshold_adjustmentが上昇する
```

## 6. Phase 3: Agent Execution Gate

### 6.1 目的

Phase 3は、OpenAyaneを文書・コード評価器から、Agent実行前後の意味変化ゲートへ拡張する段階である。

この段階で、RDEはファイル差分だけでなく、tool call、plan、external action、workspace modificationを評価対象にする。

### 6.2 主要成果物

```text
src/openayane_rde/runtime/safe_execution.py
  - sandboxed execution interface
  - timeout
  - resource limit
  - dry-run mode

src/openayane_rde/runtime/result.py
  - execution result model
  - rollback metadata

src/openayane_rde/runtime/rollback.py
  - file rollback
  - tool execution rollback descriptor

src/openayane_rde/agent/structor.py
  - plan structure extraction interface

src/openayane_rde/agent/tool_contract.py
  - tool call TaskContract builder

src/openayane_rde/policy/execution_rules.py
  - risk-specific execution policies
```

### 6.3 実行前評価

Agentがツールを実行する前に、以下を生成する。

```text
ExecutionTaskContract:
  action_type
  tool_name
  target_resource
  expected_side_effects
  allowed_side_effects
  forbidden_side_effects
  rollback_strategy
  required_user_approval
```

RDEは、これをRelationContextおよびPolicyと照合する。

```text
low risk + high trust:
  approve

medium risk + unknown context:
  approve_with_notes or human_review

high risk + external side effect:
  human_review

critical risk:
  halt
```

### 6.4 実行後評価

実行結果をAuditLogとRelationStoreに戻す。

```text
ToolCallResult
  ↓
PostExecutionDiff
  ↓
RDE post-evaluation
  ↓
PolicyDecision
  ↓
RelationStore update
  ↓
Rollback if needed
```

### 6.5 完了条件

```text
- tool callをTaskContract化できる
- 実行前RDE評価により高リスク操作を停止できる
- SafeExecutionRuntimeがdry-run / timeout / resource limitを持つ
- 実行後の結果をAuditEventとして記録できる
- rollback descriptorを保存できる
- RelationStoreがtool execution結果を履歴化できる
```

## 7. Phase 4: Institution and Accountability Layer

### 7.1 目的

Phase 4は、OpenAyaneを内部閾値だけで動く評価機構から、制度的責任・権限・本人性・組織ルールと接続できる機構へ拡張する段階である。

RDEは意味変化の評価器であり、制度判断そのものではない。Institution Layerは、RDEとPolicyDecisionを外部規範、組織規則、PoP-UID、承認フローへ接続する。

### 7.2 主要成果物

```text
src/openayane_rde/institution/rule_registry.py
  - InstitutionRuleRegistry（first-match 参照）

src/openayane_rde/institution/authority.py
  - Permission, ActorRole, ApprovalStep, ApprovalChain

src/openayane_rde/institution/pop_uid.py
  - PopUidAdapter（Protocol; 実装は呼び出し側）

src/openayane_rde/institution/accountability.py
  - DecisionProvenance / provenance_from_policy_decision

src/openayane_rde/policy/institution_bridge.py
  - decide_policy_with_institution（RDE → PolicyDecision に制度ルール・PoP を重ねる）

src/openayane_rde/audit/log.py
  - audit_event_policy_decision（監査ペイロードで RDE 分類と institution を分離）

src/openayane_rde/core/models.py PolicyDecision
  - institution_rule_id / institutional_rationale（任意参照）
```

### 7.3 制度ルールの例

```text
- 特定ファイルの変更には人間承認が必要
- 特定Actorは承認権限を持たない
- 高リスク実行は二者承認を要求する
- PoP-UIDが検証できない場合はcritical操作を停止する
- 監査ログが欠落している変更はRelationStoreへ反映しない
```

### 7.4 完了条件

```text
- PolicyDecisionがInstitutionRuleを参照できる
- actor / role / permission / approval chainを表現できる
- PoP-UID adapter interfaceが定義されている
- 承認・却下・停止の根拠をAuditLogに残せる
- RDE分類と制度判断を混同しない構造になっている
```

## 8. Phase 5: Operational Hardening and Ecosystem Integration

### 8.0 着手前提（リポジトリ現状）

```text
- Phase 1〜4 のコア（RDE / Policy / Runtime / Review / Rollback / Institution Bridge）と、
  Phase 1 フロー・実行ゲートへの制度オプション統合は main に取り込み済み。
- Phase 5 は「呼び出し・設定・アダプタ・回帰・性能・リリース規律」の層。スコープ・非目標・出口条件は
  docs/50_openayane_rde_phase5_operational_hardening_spec.md を正とする。
- 作業 Issue は #44（P5-1）〜 #54（P5-9）。原則 1 Issue = 1 branch = 1 PR。
  実行順は docs/50 §17（API / #46 は意図的に最後）。
```

### 8.1 目的

Phase 5は、OpenAyane RDEを実運用可能なライブラリまたはサービスとして安定化させる段階である。

対象は、CLI、API、外部Agent連携、CI/CD統合、性能最適化、監査ログ永続化、設定管理である。

### 8.2 主要成果物

```text
src/openayane_rde/cli/
  - evaluate
  - diff
  - audit
  - relation
  - policy-check

src/openayane_rde/server/
  - FastAPI or lightweight HTTP interface

src/openayane_rde/config/
  - config loader
  - policy config
  - model provider config

src/openayane_rde/integration/
  - OpenClaw adapter
  - GitHub PR review adapter
  - local filesystem adapter
  - editor / IDE adapter candidates

.github/workflows/
  - pytest
  - ruff
  - mypy
  - schema validation
  - golden regression
```

### 8.3 性能目標

Core処理の高速性を維持する。

```text
Core target:
  < 10ms where possible

Coreに含める:
  - relation lookup
  - lightweight policy
  - cached structural checks

Coreから除外する:
  - embedding generation
  - LLM semantic evaluation
  - full repository scan
  - remote API calls
```

### 8.4 運用上の分離

```text
synchronous path:
  low-latency gate
  cached relation context
  rule-based policy

asynchronous path:
  LLM evaluator
  long-chain drift analysis
  repository-wide scan
  model calibration
```

### 8.5 完了条件

```text
- CLIでローカル評価を実行できる
- APIとしてRDE評価を呼び出せる
- CIでgolden regressionが動く
- GitHub PRまたはローカルpatchに対してRDE評価を実行できる
- AuditLogとRelationStoreを設定で切り替えられる
- パフォーマンス測定がp50 / p95で記録される
```

## 9. Phase 6: Research Evaluation and Public Specification

### 9.1 目的

Phase 6は、OpenAyane RDEを研究評価可能な形に整理し、公開仕様・論文・ベンチマークへ展開する段階である。

実装の完成ではなく、RDEという「意味変化の監査構造」がどの範囲で有効で、どの範囲で未解決なのかを検証可能にする。

### 9.2 主要成果物

```text
specs/rde_core_spec.md
specs/task_contract_schema.md
specs/audit_event_schema.md
specs/relation_store_schema.md
benchmarks/
  markdown_drift/
  json_schema_corruption/
  python_api_drift/
  long_chain_document_corruption/
  generator_self_report_mismatch/
papers/
  openayane_rde_paper_draft.md
```

### 9.3 評価指標

```text
Unauthorized change detection rate
Critical corruption recall
Suspicious drift precision
False positive rate
Human review reduction rate
Rollback success rate
Long-chain drift detection rate
Self-report mismatch detection rate
Relation trust calibration correlation
Latency p50 / p95
Audit completeness
```

### 9.4 完了条件

```text
- RDE Coreの公開仕様がある
- TaskContract / RDEResult / AuditEvent / RelationStoreのschemaが公開可能である
- benchmark fixturesが再現可能である
- 評価指標が定義されている
- 既知の限界が明記されている
- 論文または技術報告の草稿が作成されている
```

## 10. 横断的な開発方針

### 10.1 TDDを基本にする

OpenAyane RDEは、安全性・監査性に関わるため、TDD（Test Driven Development）を基本にする。

```text
1. 期待される逸脱ケースをfixture化する
2. 期待分類をgolden resultとして定義する
3. テストを先に書く
4. 実装する
5. regressionをCIで固定する
```

**RDE観点でのテスト設計・golden の意味・分類とPolicyの分離などの詳細:** [`63_openayane_rde_testing_policy.md`](63_openayane_rde_testing_policy.md)（GitHub [#99](https://github.com/zyx-corporation/openayane-rde/issues/99)）。

### 10.2 Schema同期を維持する

Pydantic model、JSON schema、fixture、documentationの不整合を避けるため、schema同期テストを継続する。

```text
- model enumとschema enumの一致
- required fieldsの一致
- fixture JSON validation
- backward compatibility notes
```

### 10.3 RDE分類とPolicy判断を混同しない

RDEは「何が起きたか」を分類する。Policyは「どう扱うか」を決める。

この分離は、後続の制度層、組織承認、外部Agent連携に不可欠である。

### 10.4 AuditLogを先に置く

AuditLogは後付けしない。Phase 1からAuditEventを導入し、Phase 2以降のRelationStore更新の根拠として使う。

### 10.5 創造的変換を禁止しない

RDEは、すべての変化を悪とみなす機構ではない。重要なのは、許可された変換、推論的補完、疑わしい逸脱、重大な歪曲を区別することである。

```text
preserved:
  保存された要素

authorized_deviation:
  明示的に許可された変換

inferred_extension:
  文脈上推論された補完

suspicious_drift:
  疑わしい逸脱

critical_corruption:
  重大な歪曲
```

## 11. 推奨ディレクトリ構成

最終的な構成案は以下である。

```text
openayane-rde/
  docs/
    00_development_plan.md
    02_openayane_basic_design.md
    03_openayane_rde_verification_report.md
    phase1_implementation_plan.md
    11_openayane_rde_phase2_spec_2.md

  specs/
    task_contract_schema.md
    audit_event_schema.md
    relation_store_schema.md
    rde_core_spec.md

  src/openayane_rde/
    core/
      models.py
      errors.py
      ids.py

    generator/
      adapter.py
      prompt_templates.py

    diff/
      structural_base.py
      markdown_diff.py
      json_diff.py
      python_ast_diff.py

    semantic/
      delta_engine.py
      evaluator.py
      claim_tracker.py
      reference_checker.py

    rde/
      core.py
      classifier.py
      authorization.py
      scoring.py
      resonance.py
      risk.py

    policy/
      bridge.py
      rules.py
      execution_rules.py
      institution_bridge.py

    relation/
      store.py
      update.py
      context_loader.py

    audit/
      log.py
      hash_chain.py

    runtime/
      safe_execution.py
      result.py
      rollback.py

    institution/
      rule_registry.py
      authority.py
      pop_uid.py
      accountability.py

    integration/
      github_adapter.py
      openclaw_adapter.py
      filesystem_adapter.py

    cli/
      main.py

    server/
      app.py

  tests/
    unit/
    golden/
    adversarial/
    long_chain/
    integration/

  benchmarks/
    markdown_drift/
    json_schema_corruption/
    python_api_drift/
    long_chain_document_corruption/
```

## 12. Phase間依存関係

```text
Phase 0
  ↓
Phase 1 depends on:
  - concept definition
  - package skeleton
  - core model direction

Phase 2 depends on:
  - Phase1EvaluationResult
  - AuditEvent
  - StructuralDiff schema
  - SemanticDelta stub

Phase 3 depends on:
  - RelationContext Loader
  - PolicyBridge adjustment
  - AuditLog stability
  - risk classification

Phase 4 depends on:
  - PolicyBridge separation
  - Audit provenance
  - actor / subject / object modeling

Phase 5 depends on:
  - stable API boundaries
  - CLI-ready evaluation flow
  - persistent AuditLog / RelationStore

Phase 6 depends on:
  - benchmark fixtures
  - stable classifications
  - documented limitations
```

## 13. 優先順位

短期の優先順位は以下とする。

```text
P0:
  - Phase1EvaluationResultの安定化
  - StructuralDiff schema安定化
  - AuditEvent記録
  - critical_corruption halt

P1:
  - RelationStore minimal
  - update_relation_from_evaluation_result実処理化
  - allowed_delta_m matching
  - SemanticDeltaEngine Phase 2

P2:
  - long-chain drift test
  - PolicyBridge risk adjustment
  - CLI evaluate
  - GitHub PR evaluation prototype

P3:
  - SafeExecutionRuntime
  - Institution Layer interface
  - public spec
```

## 14. RDE差異検証観点による自己点検

本計画自体も、基本設計からの意味変化ΔMとして検証する。

### 14.1 保存された要素

```text
- RDEをOpenAyaneの中核評価層に置く方針
- GeneratorとEvaluatorの分離
- TaskContract中心設計
- StructuralDiffをRDEの構造化レンズとして扱う方針
- SemanticDeltaを段階的に導入する方針
- RelationStoreへのフィードバック
- PolicyとRDEの分離
- AuditLogによる責任追跡
```

### 14.2 変換された要素

基本設計ではレイヤー構成として記述されていた内容を、実装順序、成果物、完了条件、テスト戦略へ変換した。

### 14.3 補完された要素

```text
- Phase 5 Operational Hardening
- Phase 6 Research Evaluation and Public Specification
- Phase間依存関係
- 優先順位P0-P3
- CLI / API / benchmarkへの展開
```

### 14.4 未解決のまま残した要素

```text
- context_affinityの厳密な数理更新
- LLM evaluator ensembleの採用条件
- SQLite移行時のschema migration
- OpenClaw integrationの具体hook設計
- PoP-UID実装の詳細
- cryptographic audit logの方式
```

### 14.5 逸脱リスク

本計画はPhaseを広く定義しているため、Phase 4以降が過度に抽象化されるリスクがある。対策として、Phase 1とPhase 2の完了条件を優先し、Phase 3以降はPhase 2完了時点で再度RDE差異検証を行う。

### 14.6 次回更新方針

次回更新では、Phase 1とPhase 2の実装状況をもとに、以下を具体化する。

```text
- 実装済みファイルとの対応表
- 未実装項目のissue化
- Phase 2残タスクのmilestone分割
- CLI/APIの最小仕様
- GitHub PR evaluation prototypeの設計
```

## 15. 結論

OpenAyane RDEの実装は、単なる安全フィルタや差分検出器の開発ではない。中心にあるのは、生成AIが生む意味変化ΔMを、元の意図、許可された変換、保護対象、関係履歴、制度的制約との関係で監査する構造である。

Phase 1では構造差分を安定させ、Phase 2では履歴と意味ΔMを戻し、Phase 3ではAgent実行へ接続し、Phase 4以降で制度的責任と運用基盤へ拡張する。

この順序により、OpenAyaneは「生成結果を評価する道具」ではなく、「意味変化を引き受け可能にする機構」として実装される。
