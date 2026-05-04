---
title: "OpenAyane 基本設計ドキュメント"
version: "0.1-draft"
date: "2026-05-04"
author: "Tomoyuki Kano"
status: "basic design draft"
---

# OpenAyane 基本設計ドキュメント

## 0. 文書の目的

本書は、OpenAyaneをRDE（Resonant Deviation Evaluator）中心の実装可能なアーキテクチャとして再整理する基本設計文書である。

既存のOpenAyaneは、relation_store、trust、stability、context_affinity、Structor、Policy、Audit、Modification Control Flow、Safe Execution Runtime などを備えた関係ベースのエージェント安全アーキテクチャとして構想されてきた。本書では、そこにRDEを中核評価層として位置づけ、Generatorの出力、文書編集、コード変更、ツール実行、長期関係更新を一つの制御ループとして扱う。

## 1. システム目的

OpenAyaneの目的は、AIエージェントの実行を、単なる能力・記憶・人格設定ではなく、関係状態、意味変化、制度的制約に基づいて条件づけることである。

特に次を実現する。

1. 意図しない意味変化、すなわち Silent ΔM の検出
2. 生成と評価の分離
3. 許可された変換と実際の変換の比較
4. Structural Diff と Semantic Diff による監査可能性の確保
5. RDEによる逸脱分類
6. Policyによる承認、差し戻し、停止、ロールバック
7. RelationStoreへのフィードバックによる長期信頼更新
8. AuditLogによる責任追跡

## 2. 基本方針

### 2.1 Generatorを信頼しない

Generatorは変換案を生成する主体であり、最終判断者ではない。Generatorの自己申告は補助情報として扱い、Structural DiffとRDEによって検査する。

### 2.2 変換を契約化する

曖昧な指示をそのまま実行しない。ユーザー指示、文脈、対象ドメイン、リスクをもとに Task Contract を生成する。

### 2.3 実行前後の意味差分を評価する

OpenAyaneは、出力単体ではなく、変換前状態、許可された変換、生成後状態の三者関係を評価する。

### 2.4 評価結果を関係状態へ戻す

RDEの判定は、その場限りの承認判断ではなく、relation_store の trust、stability、context_affinity に反映する。

### 2.5 制度層と接続可能にする

Policyは内部閾値で動作できるが、最終的にはInstitution Layerに接続し、規範、責任、権限、本人性、組織的承認と接続できるようにする。

## 3. レイヤー構成

OpenAyaneは以下のレイヤーで構成される。

```text
Institution Layer
  ↓
Policy Layer
  ↓
RDE Layer
  ↓
Semantic Delta Layer
  ↓
Structural Diff Layer
  ↓
Generator / Agent / Tool Layer
  ↓
Safe Execution Runtime
  ↓
Audit & Relation Feedback
```

より実装寄りには次のようになる。

```text
User / External Trigger
  ↓
Intent Parser
  ↓
Task Contract Builder
  ↓
Generator Adapter
  ↓
Generated Output or Patch
  ↓
Structural Diff Engine
  ↓
Semantic Delta Engine
  ↓
RDE Core
  ↓
Policy Bridge
  ↓
Modification Control Flow
  ↓
Safe Execution Runtime / File Patch / Tool Call
  ↓
AuditLog + RelationStore Update
```

## 4. モジュール定義

### 4.1 Intent Parser

ユーザー要求、システムイベント、エージェント内部計画を解析し、操作意図を抽出する。

出力:

```yaml
Intent:
  action_type: "edit_document | modify_code | run_tool | summarize | refactor | research"
  target: "対象ファイル・対象関数・対象文書領域"
  risk_hint: "low | medium | high | critical"
  raw_instruction: "元の指示"
```

### 4.2 Task Contract Builder

IntentをRDEが評価可能な契約に変換する。

```yaml
TaskContract:
  contract_id: "uuid"
  mode: "preservation | creative | refactor | research | execution"
  target_scope:
    files: []
    symbols: []
    sections: []
  requested_action: "要求された変換"
  allowed_delta_m: []
  forbidden_delta_m: []
  protected_elements: []
  output_policy:
    require_patch: true
    require_change_report: true
    require_uncertainty_report: true
  review_policy:
    preserved: "auto_approve"
    authorized_deviation: "auto_approve_or_note"
    benign_incidental_drift: "approve_with_note"
    suspicious_drift: "human_review"
    critical_corruption: "halt"
```

### 4.3 Generator Adapter

OpenAI、Claude、Gemini、Ollama、local model、specialized tool などを抽象化する。

Generatorには、Task Contractを渡し、監査可能な出力を求める。

```yaml
GeneratorOutput:
  output_type: "full_text | patch | plan | tool_call"
  payload: "本文またはpatch"
  self_report:
    changed_elements: []
    unchanged_elements: []
    added_elements: []
    deleted_elements: []
    semantic_risk_notes: []
    uncertainty_notes: []
  model_info:
    provider: "openai | anthropic | google | local"
    model: "model-name"
    temperature: 0.2
```

### 4.4 Structural Diff Engine

変換前後の構造差分を抽出する。

対象ドメイン:

```text
Markdown:
  heading tree
  paragraphs
  definitions
  citations
  links
  tables
  code blocks

JSON:
  keys
  types
  required fields
  schema constraints
  array lengths

Python:
  AST
  imports
  function signatures
  class definitions
  control flow
  exception handling
  tests

Generic text:
  paragraph alignment
  named entities
  numbers
  dates
  references
```

出力:

```yaml
StructuralDiff:
  changed_nodes: []
  added_nodes: []
  deleted_nodes: []
  moved_nodes: []
  protected_element_changes: []
  schema_violations: []
  signature_changes: []
  reference_breaks: []
  diff_confidence: 0.0
```

### 4.5 Semantic Delta Engine

Structural Diffを足場に、意味差分を推定する。

入力:

```text
- original_state
- generated_state
- task_contract
- structural_diff
- generator_self_report
- relation_context
```

出力:

```yaml
SemanticDelta:
  delta_m_score: 0.0
  changed_claims: []
  changed_constraints: []
  changed_definitions: []
  changed_numbers: []
  changed_references: []
  changed_safety_conditions: []
  semantic_equivalence_score: 0.0
  uncertainty: 0.0
```

### 4.6 RDE Core

RDE Coreは、SemanticDeltaをTaskContract、Policy、RelationStateと照合し、逸脱分類と推奨アクションを出す。

```yaml
RDEResult:
  classification: "preserved | authorized_deviation | benign_incidental_drift | suspicious_drift | critical_corruption | creative_deviation"
  resonance_score: 0.0
  preservation_score: 0.0
  risk_level: "low | medium | high | critical"
  violated_constraints: []
  suspicious_elements: []
  required_action: "approve | approve_with_notes | request_revision | human_review | halt | rollback"
  explanation: "判定理由"
```

### 4.7 Policy Bridge

Policy BridgeはRDEの判定を実行制御へ変換する。

```text
Preserved → approve
Authorized Deviation → approve or approve_with_notes
Benign Incidental Drift → approve_with_notes
Suspicious Drift → human_review or request_revision
Critical Corruption → halt or rollback
Creative Deviation → modeに応じてapprove / review
```

### 4.8 Modification Control Flow

変更提案、RDE評価、承認、適用、ロールバックを管理する。

```text
propose_change
  ↓
run_diff
  ↓
run_rde
  ↓
decide
  ↓
apply_or_reject
  ↓
audit
```

### 4.9 Safe Execution Runtime

外部ツール、ファイルシステム、ネットワーク、メール、カレンダー、決済などの実行をsandbox、権限、timeout、resource limitで制御する。

### 4.10 Relation Store

Agent、User、Tool、Document、Workspace間の関係状態を保存する。

```yaml
RelationState:
  subject_id: "agent-or-user"
  object_id: "user-tool-document-workspace"
  trust: 0.0
  stability: 0.0
  context_affinity: 0.0
  interaction_count: 0
  last_delta_m: 0.0
  delta_m_history_summary: {}
  last_updated_at: "timestamp"
```

### 4.11 Audit & Responsibility Engine

すべての判断、差分、RDE分類、Policy決定、実行、ロールバックを記録する。

```yaml
AuditEvent:
  event_id: "uuid"
  timestamp: "iso8601"
  actor: "agent/user/tool"
  task_contract_id: "uuid"
  rde_result_id: "uuid"
  action: "approve | halt | rollback | execute"
  hash_before: "sha256"
  hash_after: "sha256"
  explanation: "why"
```

## 5. RDE判定アルゴリズムの基本形

```python
def evaluate_rde(original, generated, contract, relation_state, policy):
    structural = structural_diff(original, generated, contract)
    semantic = semantic_delta(original, generated, contract, structural)

    preservation = score_preservation(semantic, contract.protected_elements)
    authorization = score_authorization(semantic, contract.allowed_delta_m, contract.forbidden_delta_m)
    resonance = score_resonance(semantic, relation_state, contract)
    risk = score_risk(structural, semantic, contract)

    classification = classify(
        preservation=preservation,
        authorization=authorization,
        resonance=resonance,
        risk=risk,
        mode=contract.mode,
    )

    action = policy_decide(classification, risk, contract.review_policy)

    return RDEResult(
        classification=classification,
        resonance_score=resonance,
        preservation_score=preservation,
        risk_level=risk,
        required_action=action,
    )
```

## 6. Relation update

RDE結果はrelation_storeに戻す。

基本方針:

```text
Preserved:
  stability上昇
  trust小幅上昇

Authorized Deviation:
  context_affinityが高い場合、trust小幅上昇
  stabilityは変化量に応じて更新

Benign Incidental Drift:
  trust維持または微減
  drift patternとして記録

Suspicious Drift:
  trust微減
  stability微減
  人間レビュー結果まで保留

Critical Corruption:
  trust大幅低下
  stability大幅低下
  当該文脈でreview thresholdを上げる
```

更新式の初期案:

\[
trust_{t+1} = clip(trust_t + \alpha \cdot q_{rde} \cdot context\_affinity_t - \beta \cdot risk)
\]

\[
stability_{t+1} = EMA(stability_t, 1 - normalized(|\Delta M_t|))
\]

\[
context\_affinity_{t+1} = update\_context\_summary(context\_affinity_t, current\_context)
\]

context_affinity の厳密更新は未確定であり、Phase 2では近似、Phase 3で分布的更新を導入する。

## 7. Generator用システムプロンプト方針

Generatorには、RDEが評価しやすい出力を求める。

```text
You are a generator, not the final authority.
Your task is to transform the given document only within the explicitly allowed scope.
Preserve all protected elements unless explicitly authorized.
Return a patch or final output plus a structured change report.
Do not silently rewrite, normalize, omit, merge, simplify, or reinterpret content outside the requested scope.
If a useful change is outside the requested scope, list it as a suggestion instead of applying it.
```

日本語版:

```text
あなたは生成器であり、最終判断者ではない。
明示的に許可された範囲内でのみ変換すること。
保護対象は、明示的に許可されない限り変更してはならない。
出力は本文またはpatchに加えて、構造化された変更レポートを含めること。
要求範囲外の書き換え、正規化、省略、統合、単純化、再解釈を黙って行ってはならない。
有用そうな変更でも、要求範囲外であれば本文には適用せず、suggestionsに列挙すること。
```

## 8. 基本フロー

### 8.1 文書編集フロー

```text
User: この章を読みやすくして。ただし主張と引用は変えない。
  ↓
Intent Parser: style_edit
  ↓
Task Contract Builder:
  allowed_delta_m = 文体・冗長性・接続表現
  forbidden_delta_m = 主張・引用・定義・数値
  ↓
Generator Output + self_report
  ↓
Markdown Structural Diff
  ↓
Semantic Delta Engine
  ↓
RDE Classification
  ↓
Policy Decision
  ↓
Apply / Review / Halt
```

### 8.2 コード変更フロー

```text
User: エラー処理を追加して。ただしアルゴリズムは変えない。
  ↓
Task Contract:
  allowed = try/except, logging, validation
  forbidden = formula, API, tests removal
  ↓
Generator returns patch
  ↓
Python AST Diff + tests
  ↓
RDE
  ↓
Policy
```

### 8.3 ツール実行フロー

```text
Agent plans tool call
  ↓
Structor evaluates plan structure
  ↓
Task Contract for execution
  ↓
RDE checks relation state + context_affinity + risk
  ↓
Policy Bridge
  ↓
Safe Execution Runtime
  ↓
AuditLog and RelationStore update
```

## 9. 非機能要件

### 9.1 レイテンシ

Core判定は高速であるべきである。

```text
Core処理: < 10msを目標
対象: relation lookup, lightweight policy, cached structural checks
除外: embedding生成, LLM semantic evaluation, full repository scan
```

重い処理は非同期、キャッシュ、バッチ、またはレビュー前処理に逃がす。

### 9.2 監査性

すべての承認、停止、差し戻し、ロールバックはAuditLogに残す。

### 9.3 非侵入性

OpenClawまたは外部Agentに統合する場合、公式lifecycle / plugin / hookを優先し、upstream変更に強くする。

### 9.4 安全性

高リスク操作はRDEとPolicyの両方を通過しなければ実行しない。

### 9.5 拡張性

Structural Diff Engineはドメインプラグイン化する。

## 10. Phase設計

### Phase 0: Concept freeze

- RDE定義
- Task Contract定義
- 判定分類
- OpenAyane既存モジュールとの対応整理

### Phase 1: Structural RDE MVP

対象:

```text
Markdown
JSON
Python
```

実装:

```text
TaskContract
GeneratorOutput
StructuralDiff
RDEResult minimal
AuditLog minimal
```

目標:

```text
許可外の構造変更を検出する
Generator自己申告と実diffの不一致を検出する
```

### Phase 2: Semantic ΔM + Relation Feedback

実装:

```text
SemanticDeltaEngine
RelationStore update
trust/stability/context_affinity provisional update
LLM evaluator ensemble
```

目標:

```text
意味変化の疑義分類
relationに基づくレビュー閾値調整
```

### Phase 3: Agent Execution Gate

実装:

```text
Structor integration
Policy Bridge
Safe Execution Runtime
Tool call gating
Rollback manager
```

目標:

```text
文書編集だけでなく、ツール実行前の関係・意味評価を行う
```

### Phase 4: Institution Layer

実装:

```text
PoP-UID連携
DAO / organization policy
external accountability
normative rule registry
```

目標:

```text
内部閾値ではなく、外部制度的根拠に基づくPolicy判断
```

## 11. 推奨ディレクトリ構成

```text
openayane/
  core/
    task_contract.py
    rde_result.py
    relation_state.py
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
    claim_tracker.py
    reference_checker.py
  rde/
    core.py
    classifier.py
    resonance.py
    risk.py
  policy/
    bridge.py
    rules.py
  relation/
    store.py
    update.py
  audit/
    log.py
    hash_chain.py
  runtime/
    safe_execution.py
    rollback.py
  tests/
    unit/
    integration/
    adversarial/
```

## 12. テスト戦略

### 12.1 Unit Tests

- TaskContract生成
- StructuralDiff検出
- RDE分類
- Policy決定
- RelationStore更新

### 12.2 Golden Tests

既知の入力・出力・期待分類を固定し、RDEが安定して同じ判断を返すかを見る。

### 12.3 Adversarial Tests

- 数値だけが微妙に変わる
- JSON keyが消える
- 引用が外れる
- 定義文が弱まる
- Python function signatureが変わる
- Generator self_reportが嘘をつく

### 12.4 Long-chain Tests

20回、50回、100回の編集連鎖でSilent ΔMを検出できるかを見る。

### 12.5 Human Review Calibration

Suspicious Drift判定と人間判断の一致率を測る。

## 13. 評価指標

```text
Unauthorized change detection rate
False positive rate
Critical corruption recall
Suspicious drift precision
Human review reduction rate
Rollback success rate
Relation trust calibration correlation
Latency p50 / p95
Audit completeness
```

## 14. リスクと対策

### 14.1 Semantic Diffの不完全性

対策: Structural Diff、ルール、テスト、LLM evaluator、人間レビューを組み合わせる。

### 14.2 Generator制約による創造性低下

対策: mode別に許可ΔMを変える。

### 14.3 Evaluator drift

対策: RDEをLLM単体にしない。複数評価器と構造検査を併用する。

### 14.4 context_affinity poisoning

対策: Phase 2では保守的に扱い、Phase 3でmax/mean hybridと分布更新を導入する。

### 14.5 過剰停止

対策: classificationとriskを分離し、低リスクのBenign Driftは承認可能にする。

## 15. 受け入れ基準

Phase 1 MVPの受け入れ基準:

1. Markdownで見出し、引用、定義、数値の許可外変更を検出できる。
2. JSONでschema key、type、required fieldの破壊を検出できる。
3. Pythonでfunction signature、import、主要AST変更を検出できる。
4. Generator self_reportと実diffの不一致を記録できる。
5. RDEResultがpreserved / authorized / suspicious / criticalを返せる。
6. AuditLogにTaskContract、Diff、RDE、Policy decisionが保存される。
7. 高リスクcritical corruptionで自動適用が停止する。

## 16. 結論

OpenAyaneの基本設計は、RDEを中心に置くことで、エージェント安全を「危険行為の禁止」から「意味変化の監査と制御」へ拡張する。

RDEはOpenAyaneの外側で概念として確立され、OpenAyaneの内側で実装として機能する。

これにより、Ayaneは単なるAgent実行基盤ではなく、生成系の意味変化を観測し、分類し、制度的に処理する知性基盤になる。
