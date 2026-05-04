# OpenAyane Phase 2 詳細仕様書：履歴参照ループと意味ΔM基盤の実装

## 0. 文書情報

文書名：OpenAyane Phase 2 詳細仕様書
副題：履歴参照ループと意味ΔM基盤の実装
版：0.2-draft
作成日：2026-05-04
作成者：Tomoyuki Kano
対象リポジトリ：`git@github.com:zyx-corporation/openayane-rde.git`
前提フェーズ：Phase 1 Structural RDE MVP 完了版

## 1. 改訂方針

本改訂は、Phase 1最終修正を前提にPhase 2仕様を再整理するものである。

Phase 1最終修正により、以下が実装済みとなった。

```text
- Phase1EvaluationResult
- task_contract / generator_output / relation_context の同梱
- structural_diff / semantic_delta / rde_result / policy_decision / audit_event の集約
- update_relation_from_evaluation_result() のstub
- RelationUpdateSummary
- CI workflow
- Schema / Model enum同期テスト
- schema_fixtures JSON validation
```

したがって、Phase 2では、個別の `RDEResult` や `AuditEvent` を主入力にするのではなく、**Phase1EvaluationResultを履歴更新・意味ΔM拡張・RelationStore更新の標準入力単位**として扱う。

```text
Phase 1:
  評価単位 Phase1EvaluationResult を生成する

Phase 2:
  Phase1EvaluationResult を RelationStore と Semantic ΔM 基盤へ流す
```

これにより、Phase 2はPhase 1の延長ではなく、OpenAyaneを履歴を持つ意味変化監査機構へ進める段階として定義される。

## 2. Phase 2の位置づけ

Phase 1では、OpenAyane RDEの最小構成として、TaskContract、GeneratorOutput、StructuralDiff、SemanticDelta stub、RDEResult、PolicyDecision、AuditEvent、Markdown / JSON / Python AST Diff、RDE最小分類器、PolicyBridge、AuditLog JSONLが実装された。

Phase 1の最終到達点は、**Structural RDE MVP + Phase2接続可能な評価単位生成**である。

つまり、Phase 1は以下を実現した。

```text
入力:
  original
  generator_output
  task_contract
  relation_context optional

処理:
  StructuralDiff
  SemanticDelta stub
  RDE evaluation
  PolicyDecision
  AuditEvent optional

出力:
  Phase1EvaluationResult
```

Phase 2では、この `Phase1EvaluationResult` を出発点として、以下を実装する。

```text
Phase1EvaluationResult
  ↓
RelationStore Update
  ↓
RelationContext Loader
  ↓
TaskContract / RDE / Policy への再入力
```

Phase 2の核心は、RDEを単に賢くすることではない。RDE評価結果をOpenAyane機構に流し込み、過去のΔMを未来の判断条件へ戻すことである。

## 3. Phase 2の目的

Phase 2の目的は、OpenAyaneを単発のStructural RDE評価ループから、履歴を持つ意味変化監査機構へ拡張することである。

具体的には、以下を実現する。

```text
1. Phase1EvaluationResultをPhase 2の標準入力単位にする
2. RelationStore minimalを実装する
3. update_relation_from_evaluation_result() をstubから実処理へ拡張する
4. AuditEventとRDEResultを根拠にRelationStateを更新する
5. RelationContext Loaderを実データ対応にする
6. self_report mismatchやcritical_corruptionを履歴に蓄積する
7. 履歴に応じてrisk adjustmentやreview thresholdを変化させる
8. allowed_delta_mと実diffの照合を強化する
9. SemanticDeltaEngineを構造差分由来の意味候補抽出器へ拡張する
10. Long-chain drift testを実装し、drift蓄積を観測する
```

## 4. Phase 2の非目的

Phase 2は、OpenAyaneの完全版ではない。

以下はPhase 2の非目的である。

```text
- 完全な意味理解
- LLM evaluator ensembleの本格運用
- 外部Agentの実ツール実行制御
- Safe Execution Runtime完全実装
- Institution Layer完全実装
- PoP-UID連携
- 暗号学的AuditLog
- 本格的な組織Policyエンジン
```

Phase 2は、履歴参照と意味ΔM推定の基盤を作る段階である。

## 5. 基本原則

### 5.1 RDEは評価器である

Phase 2でも、RDEは評価器であり続ける。

RDEは、意味変化ΔMを評価し、分類し、推奨アクションを返す。

RDEは以下を行わない。

```text
- 変更を適用しない
- ファイルを書き換えない
- RelationStoreを直接更新しない
- Policyの最終決定を行わない
- 実行副作用を起こさない
```

### 5.2 OpenAyaneは機構である

OpenAyaneは、RDEを中核評価器として含む機構である。

Phase 2では、OpenAyane機構として以下を強化する。

```text
- 評価結果の集約
- AuditLog記録
- RelationStore更新
- 履歴参照
- 次回判断条件への反映
```

### 5.3 Phase1EvaluationResultを履歴更新の単位にする

Phase 2では、RelationStore更新の基本入力を `Phase1EvaluationResult` とする。

理由は、`Phase1EvaluationResult` が以下をすべて含むためである。

```text
- task_contract
- generator_output
- relation_context optional
- structural_diff
- semantic_delta
- rde_result
- policy_decision
- audit_event optional
```

この構造により、RelationStore更新時に、評価の文脈、生成主体、差分、RDE分類、Policy判断、Audit根拠を再取得する必要がなくなる。

### 5.4 AuditLogとRelationStoreを分離する

AuditLogとRelationStoreは異なる。

```text
AuditLog:
  過去に何が起きたかの不可逆的記録

RelationStore:
  AuditLogまたはPhase1EvaluationResultから抽出された関係状態
```

AuditLogは事実の記録である。RelationStoreは、その事実から計算された状態である。

RelationStoreを更新する場合、可能な限り根拠となるAuditEventまたはPhase1EvaluationResultを参照可能にする。

### 5.5 履歴は判断を補助するが、絶対化しない

RelationStoreは過去のdrift patternを蓄積するが、それを絶対視してはならない。

過去の失敗を一般化しすぎると、過剰停止、不当な不信、文脈境界の硬直化を生む。逆に、履歴を軽視しすぎると、同じSilent ΔMが繰り返される。

Phase 2では、保守的な更新と明示的な監査可能性を重視する。

## 6. Phase 2全体フロー

Phase 2の主要フローは以下である。

```text
User / External Trigger
  ↓
Intent Parser
  ↓
RelationContext Loader
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
AuditLog optional
  ↓
Phase1EvaluationResult
  ↓
RelationStore Update
  ↓
Historical Context Feedback
  ↺ RelationContext Loader / Task Contract Builder / RDE Core / Policy Bridge
```

Phase 1との差分は以下である。

```text
Phase 1:
  StructuralDiff中心
  SemanticDeltaはstub
  RelationContextはneutral stub
  AuditLogは記録のみ
  Phase1EvaluationResultを返す

Phase 2:
  Phase1EvaluationResultを履歴更新の入力にする
  SemanticDeltaは構造差分由来の意味候補抽出器へ拡張
  RelationStoreを最小実装
  AuditEventまたは評価結果からRelationStateを更新
  RelationContext Loaderが実データを返す
  RDE / PolicyがRelationContextを参照してriskを調整する
```

## 7. Phase 2成果物一覧

Phase 2で作成・更新する成果物は以下である。

```text
src/openayane_rde/core/models.py
  - RelationStoreRecord
  - DriftPattern
  - GeneratorReliabilityProfile
  - DocumentFragilityProfile
  - RiskAdjustment
  - AllowedDeltaMatchResult

src/openayane_rde/relation/store.py
  - JSONまたはSQLiteベースのRelationStore
  - load / save / get / upsert

src/openayane_rde/relation/update.py
  - update_relation_from_evaluation_result 実処理化
  - update_from_rde_result
  - update_drift_patterns
  - update_profiles

src/openayane_rde/relation/context_loader.py
  - neutral stubから実RelationStore参照へ拡張

src/openayane_rde/rde/authorization.py
  - allowed_delta_m matching

src/openayane_rde/rde/scoring.py
  - relation adjustment
  - history-aware risk scoring

src/openayane_rde/policy/bridge.py
  - relation_contextに基づくpolicy adjustment

src/openayane_rde/semantic/delta_engine.py
  - protected diff由来のSemanticDelta候補抽出強化

tests/unit/test_relation_store.py
  - RelationStore load/save/upsert

tests/unit/test_relation_update.py
  - Phase1EvaluationResultからRelationStore更新

tests/unit/test_relation_context_loader.py
  - RelationStoreからRelationContext読み込み

tests/unit/test_allowed_delta_matching.py
  - allowed_delta_m照合

tests/unit/test_semantic_delta_engine_phase2.py
  - StructuralDiff由来の意味候補抽出

tests/long_chain/test_markdown_long_chain_drift.py
  - long-chain drift蓄積テスト
```

## 8. Phase1EvaluationResultの扱い

### 8.1 現状

Phase 1最終版では、`Phase1EvaluationResult` は以下を含む。

```python
class Phase1EvaluationResult(BaseModel):
    task_contract: TaskContract
    generator_output: GeneratorOutput
    relation_context: RelationContext | None = None
    structural_diff: StructuralDiff
    semantic_delta: SemanticDelta
    rde_result: RDEResult
    policy_decision: PolicyDecision
    audit_event: AuditEvent | None = None
```

これはPhase 2の標準入力として十分である。

### 8.2 Phase 2要件

Phase 2では、以下の関数が `Phase1EvaluationResult` を直接受け取る。

```python
def update_relation_from_evaluation_result(
    result: Phase1EvaluationResult,
    store: RelationStore,
) -> RelationUpdateSummary:
    ...
```

Phase 1時点では、同名関数はstubとして存在している。Phase 2ではこれを実処理へ置き換える。

### 8.3 受け入れ基準

```text
- Phase1EvaluationResultからRelationStoreを更新できる
- task_contract / generator_output / rde_result / structural_diff を再取得せずに利用できる
- audit_eventが存在する場合、RelationStoreRecordにlast_audit_event_idを記録できる
- audit_eventが存在しない場合でも、非監査評価として更新可否を制御できる
```

## 9. RelationStore Minimal

### 9.1 目的

RelationStoreは、AuditLogまたはPhase1EvaluationResultから抽出された関係状態を保存する。

Phase 2では、以下を最小実装する。

```text
- subject_id / object_idごとのRelationState保存
- generator reliability profile
- document fragility profile
- drift pattern蓄積
- critical_corruption count
- suspicious_drift count
- self_report_mismatch count
- review threshold adjustment
```

### 9.2 保存形式

Phase 2では、実装容易性を優先してJSONファイルまたはSQLiteを選択する。

初期推奨はJSONである。

```text
.relation_store/relation_state.json
```

JSON実装が安定した後、SQLiteへ移行できる。

```text
.relation_store/relation_store.sqlite3
```

### 9.3 RelationStore interface

```python
class RelationStore(Protocol):
    def get(self, subject_id: str, object_id: str) -> RelationStoreRecord | None:
        ...

    def upsert(self, record: RelationStoreRecord) -> None:
        ...

    def load_context(self, subject_id: str, object_id: str) -> RelationContext:
        ...
```

### 9.4 JSONRelationStore

```python
class JSONRelationStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def get(self, subject_id: str, object_id: str) -> RelationStoreRecord | None:
        ...

    def upsert(self, record: RelationStoreRecord) -> None:
        ...

    def load_all(self) -> dict[str, RelationStoreRecord]:
        ...

    def save_all(self, records: dict[str, RelationStoreRecord]) -> None:
        ...
```

## 10. RelationStoreRecord

```python
class RelationStoreRecord(BaseModel):
    relation_id: str
    subject_id: str
    object_id: str
    relation_type: Literal[
        "generator-document",
        "agent-document",
        "user-agent",
        "tool-workspace",
        "domain-policy",
    ]
    trust: float = Field(ge=0.0, le=1.0)
    stability: float = Field(ge=0.0, le=1.0)
    context_affinity: float = Field(ge=0.0, le=1.0)
    interaction_count: int
    critical_corruption_count: int
    suspicious_drift_count: int
    self_report_mismatch_count: int
    drift_patterns: list[DriftPattern]
    generator_reliability_profile: GeneratorReliabilityProfile | None
    document_fragility_profile: DocumentFragilityProfile | None
    review_threshold_adjustment: float
    last_delta_m: float
    last_audit_event_id: str | None
    updated_at: datetime
```

## 11. DriftPattern

```python
class DriftPattern(BaseModel):
    pattern_id: str
    kind: Literal[
        "citation_weakening",
        "citation_deletion",
        "number_change",
        "definition_shift",
        "constraint_omission",
        "schema_key_deletion",
        "required_field_deletion",
        "signature_change",
        "test_deletion",
        "self_report_mismatch",
        "other",
    ]
    count: int
    severity: RiskLevel
    examples: list[str]
    last_seen_at: datetime
```

## 12. GeneratorReliabilityProfile

```python
class GeneratorReliabilityProfile(BaseModel):
    generator_id: str
    total_outputs: int
    self_report_mismatch_count: int
    critical_corruption_count: int
    suspicious_drift_count: int
    preserved_count: int
    authorized_deviation_count: int
    reliability_score: float = Field(ge=0.0, le=1.0)
```

初期計算式：

```text
reliability_score = clip01(
  1.0
  - 0.15 * critical_corruption_count
  - 0.08 * self_report_mismatch_count
  - 0.05 * suspicious_drift_count
  + 0.01 * preserved_count
)
```

この式は暫定であり、Phase 2では観測可能性を優先する。

## 13. DocumentFragilityProfile

```python
class DocumentFragilityProfile(BaseModel):
    document_id: str
    total_edits: int
    protected_change_count: int
    citation_break_count: int
    number_change_count: int
    definition_shift_count: int
    fragility_score: float = Field(ge=0.0, le=1.0)
```

初期計算式：

```text
fragility_score = clip01(
  0.10 * protected_change_count
  + 0.15 * citation_break_count
  + 0.12 * number_change_count
  + 0.10 * definition_shift_count
)
```

## 14. RelationStore Update

### 14.1 目的

`Phase1EvaluationResult` からRelationStoreを更新する。

### 14.2 推奨API

```python
def update_relation_from_evaluation_result(
    result: Phase1EvaluationResult,
    store: RelationStore | None = None,
) -> RelationUpdateSummary:
    ...
```

Phase 1では `store` なしのstubだった。Phase 2では `store` を渡した場合に実更新を行う。

### 14.3 RelationUpdateSummary

Phase 1では以下の最小モデルが存在する。

```python
class RelationUpdateSummary(BaseModel):
    context: RelationContext
    updated: bool = False
    message: str = ""
```

Phase 2では拡張する。

```python
class RelationUpdateSummary(BaseModel):
    context: RelationContext
    updated: bool
    relation_id: str | None = None
    trust_before: float | None = None
    trust_after: float | None = None
    stability_before: float | None = None
    stability_after: float | None = None
    review_threshold_adjustment_before: float | None = None
    review_threshold_adjustment_after: float | None = None
    updated_patterns: list[str] = Field(default_factory=list)
    message: str = ""
```

### 14.4 更新規則の初期案

Phase 2では、厳密な数理モデルではなく、保守的なルールベースでよい。

```text
preserved:
  trust +0.01
  stability +0.01

authorized_deviation:
  trust +0.005
  stability unchanged or +0.005

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

### 14.5 更新式

```python
def clip01(x: float) -> float:
    return max(0.0, min(1.0, x))

trust_next = clip01(trust_current + trust_delta)
stability_next = clip01(stability_current + stability_delta)
review_threshold_adjustment_next = clip01(
    review_threshold_adjustment_current + threshold_delta
)
```

### 14.6 AuditEventの扱い

`Phase1EvaluationResult.audit_event` が存在する場合、`last_audit_event_id` に記録する。

存在しない場合は、次のいずれかを選択する。

```text
Option A:
  RelationStore更新を行わない

Option B:
  non-audited updateとして更新するが、messageに明記する
```

Phase 2初期ではOption Aを推奨する。

理由は、RelationStoreの更新根拠をAuditLogに接続し、履歴の監査可能性を守るためである。

## 15. RelationContext Loader拡張

### 15.1 現状

Phase 1では、RelationContext Loaderはneutral stubを返す。

```python
trust=0.5
stability=0.5
context_affinity=0.5
drift_patterns=[]
```

### 15.2 Phase 2仕様

Phase 2では、RelationStoreから対象関係を読み込む。

```python
def load_relation_context(
    subject_id: str,
    object_id: str,
    store: RelationStore,
) -> RelationContext:
    ...
```

### 15.3 RelationContext生成規則

RelationStoreRecordから以下を抽出する。

```text
trust
stability
context_affinity
interaction_count
last_delta_m
drift_patterns
review_threshold_adjustments
```

### 15.4 デフォルト

該当レコードがない場合はneutral contextを返す。

```text
trust=0.5
stability=0.5
context_affinity=0.5
interaction_count=0
drift_patterns=[]
```

## 16. Risk Adjustment

### 16.1 目的

履歴に応じてRDEまたはPolicyのリスク評価を補正する。

### 16.2 初期規則

```text
self_report_mismatch_count >= 3:
  self_report_mismatch_score +0.1
  review threshold +0.1

critical_corruption_count >= 1:
  risk_levelを最低highに引き上げる

same drift pattern count >= 3:
  suspicious_driftをhuman_reviewへ固定

document_fragility_score >= 0.7:
  protected_elements変更のriskを一段階上げる

generator reliability_score <= 0.3:
  auto_approveを禁止
```

### 16.3 実装位置

候補は2つある。

```text
RDE scoring:
  risk scoreを補正する

Policy Bridge:
  actionを保守側へ補正する
```

Phase 2では、Policy Bridge側での補正を優先する。

理由は、RDE評価そのものと、機構としての実行判断を分けるためである。

```text
RDE:
  現在の意味変化を評価する

Policy Bridge:
  履歴と制度的制約を踏まえ、実行判断を補正する
```

## 17. allowed_delta_m matching強化

### 17.1 現状の問題

Phase 1分類器では、変更が存在し、`contract.allowed_delta_m` が空でなければ、protected changeがない限り `authorized_deviation` に寄りやすい。

これはMVPとしては単純でよいが、Phase 2では不十分である。

### 17.2 Phase 2仕様

`allowed_delta_m` と実際の差分内容を照合する。

```python
def match_allowed_delta(
    structural_diff: StructuralDiff,
    semantic_delta: SemanticDelta,
    contract: TaskContract,
) -> AllowedDeltaMatchResult:
    ...
```

### 17.3 AllowedDeltaMatchResult

```python
class AllowedDeltaMatchResult(BaseModel):
    matched_changes: list[str]
    unmatched_changes: list[str]
    forbidden_matches: list[str]
    match_score: float = Field(ge=0.0, le=1.0)
    explanation: str
```

### 17.4 初期実装

Phase 2では、まず文字列・ルールベースでよい。

対象：

```text
changed_nodes.description
protected_element_changes.description
semantic_delta.changed_definitions
semantic_delta.changed_numbers
semantic_delta.changed_references
```

規則：

```text
- allowed_delta_mに対応するキーワードが含まれる変更はmatched
- forbidden_delta_mに対応するキーワードが含まれる変更はforbidden
- protected_elements変更は原則unmatchedまたはforbidden扱い
- match_scoreが低い場合、authorized_deviationへ分類しない
```

### 17.5 受け入れ基準

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

## 18. SemanticDeltaEngine Phase 2

### 18.1 目的

Phase 1のSemanticDeltaはstubである。Phase 2では、StructuralDiff由来の意味候補をより明示的に抽出する。

### 18.2 対象

```text
changed_claims
changed_constraints
changed_definitions
changed_numbers
changed_references
changed_safety_conditions
```

### 18.3 初期実装

StructuralDiffから以下のように抽出する。

```text
Markdown:
  definition diff -> changed_definitions
  number diff -> changed_numbers
  citation/link deletion -> changed_references
  heading deletion in protected section -> changed_claims候補

JSON:
  required field deletion -> changed_constraints
  type change -> changed_constraints
  schema violation -> changed_safety_conditions候補

Python:
  function signature change -> changed_constraints
  public API deletion -> changed_constraints
  test deletion -> changed_safety_conditions
  exception handling removal -> changed_safety_conditions
```

### 18.4 LLM evaluator

Phase 2ではLLM evaluatorは必須ではない。

ただし、オプションとしてinterfaceだけ定義してもよい。

```python
class SemanticEvaluator(Protocol):
    def evaluate(self, original: str, generated: str, context: dict) -> SemanticDelta:
        ...
```

実運用はPhase 3以降でよい。

## 19. Long-chain Drift Test

### 19.1 目的

OpenAyaneの履歴参照ループが、単発では軽微なdriftの蓄積を検出できるかを検証する。

### 19.2 テスト概要

```text
original.md
  ↓ edit 1
version_1.md
  ↓ edit 2
version_2.md
  ...
  ↓ edit 20
version_20.md
```

各編集で、わずかな数値変更、引用削除、定義弱化、制約省略などを混入する。

### 19.3 測定項目

```text
- cumulative_delta_m_score
- critical_corruption_count
- suspicious_drift_count
- self_report_mismatch_count
- review_threshold_adjustment
- document_fragility_score
```

### 19.4 受け入れ基準

```text
- 同じ種類のdriftが3回以上発生するとdrift_patternとして記録される
- document_fragility_scoreが上昇する
- review_threshold_adjustmentが上昇する
- 以後の類似変更でauto_approveが抑制される
```

## 20. CI / Schema同期の扱い

Phase 1最終版でCIとSchema同期テストは導入済みである。

Phase 2では、これらを維持し、RelationStore、allowed_delta_m matching、SemanticDelta Phase 2のテストを追加する。

### 20.1 既存CI

```text
pytest
ruff check src tests
mypy src
Python 3.11 / 3.12
```

### 20.2 追加すべきテスト

```text
tests/unit/test_relation_store.py
tests/unit/test_relation_update.py
tests/unit/test_relation_context_loader.py
tests/unit/test_allowed_delta_matching.py
tests/unit/test_semantic_delta_engine_phase2.py
tests/long_chain/test_markdown_long_chain_drift.py
```

### 20.3 Schema同期

Phase 2では、以下の追加モデルが出る場合、Schema同期テストを拡張する。

```text
RelationStoreRecord
DriftPattern
AllowedDeltaMatchResult
RelationUpdateSummary
```

## 21. Phase 2 受け入れ基準

Phase 2は、以下を満たした時点で完了とする。

```text
1. Phase1EvaluationResultを標準入力としてRelationStoreを更新できる
2. RelationStore minimalが実装されている
3. AuditEventがある評価のみRelationStore更新対象にできる
4. RelationContext LoaderがRelationStoreから実データを返せる
5. RDEまたはPolicyがRelationContextに基づくrisk adjustmentを行える
6. allowed_delta_m matchingが実装され、明らかな不一致をsuspicious_driftへ送れる
7. SemanticDeltaEngineがStructuralDiff由来の意味候補を抽出できる
8. Long-chain drift testが少なくとも20回編集を扱える
9. 同一drift patternが複数回発生した場合、RelationStoreに蓄積される
10. CIでpytest / ruff / mypyが通る
```

## 22. 実装優先順位

### Priority 1

```text
- RelationStore minimal
- update_relation_from_evaluation_result 実処理化
- RelationContext Loader実データ対応
```

理由：OpenAyaneの履歴参照ループを実体化する。

### Priority 2

```text
- RelationUpdateSummary拡張
- DriftPattern
- GeneratorReliabilityProfile
- DocumentFragilityProfile
```

理由：履歴を意味ある状態として保存する。

### Priority 3

```text
- allowed_delta_m matching
- Policy risk adjustment
```

理由：authorized_deviationの過剰承認を抑制する。

### Priority 4

```text
- SemanticDeltaEngine Phase 2
- Long-chain drift test
```

理由：意味ΔM基盤と履歴蓄積評価を開始する。

## 23. RDE差異検証

### 23.1 保存された要素

Phase 2仕様は、RDEを評価器、OpenAyaneを機構として扱う基本方針を保存している。

また、Phase 1のStructural RDE MVPを否定せず、その上に履歴参照ループとSemantic ΔM基盤を追加する構成を保存している。

### 23.2 変換された要素

論文上の「Semantic ΔM + Relation Feedback」という構想を、実装可能なRelationStore、RelationContext Loader、risk adjustment、allowed_delta_m matching、long-chain testへ変換した。

今回の改訂では、Phase 2の入力単位を個別のRDEResultではなくPhase1EvaluationResultへ変更した。これは、Phase 1最終実装によって評価単位が明確化されたことに基づくAuthorized Transformationである。

### 23.3 補完された要素

以下を補完した。

```text
- Phase1EvaluationResultを標準入力とする設計
- RelationStore interface
- JSONRelationStore案
- AuditEventがない場合の更新方針
- RelationUpdateSummary拡張案
- Risk Adjustmentの実装位置
- Phase 1最終修正との差分整理
```

### 23.4 未解決のまま残した要素

以下はPhase 2でも未解決として残る。

```text
- 完全なSemantic Diff
- LLM evaluator ensemble
- Institution Layer
- Safe Execution Runtime完全実装
- PoP-UID連携
- 暗号学的AuditLog
- 厳密なcontext_affinity更新理論
```

### 23.5 逸脱リスク

Phase 2ではRelationStore更新を導入するため、履歴による過剰な自己強化リスクがある。

例えば、一度のcritical corruptionが特定Generatorや文書への過剰な不信を生み、その後の正当な変更まで過剰停止する可能性がある。

したがって、Phase 2のRelationStore更新は保守的かつ監査可能でなければならない。

また、Phase1EvaluationResultが豊富な情報を持つため、それを「真実の完全記録」と誤認するリスクもある。Phase1EvaluationResultは評価単位であり、最終的な制度的真実ではない。AuditLog、Human Review、RelationStore更新と組み合わせて扱う必要がある。

### 23.6 次回更新方針

Phase 2実装後は、Phase 3として以下を検討する。

```text
Phase 3:
  Agent Execution Gate
  Safe Execution Runtime
  Tool call gating
  Rollback Manager
  Human Review Workflow
  Optional LLM Semantic Evaluator
```

## 24. 結論

Phase 2は、OpenAyaneを単発のStructural RDE評価ループから、履歴を持つ意味変化監査機構へ進める段階である。

Phase 1でRDE評価器の最小形と評価単位 `Phase1EvaluationResult` は成立した。Phase 2では、その評価単位をRelationStoreに流し込み、過去のΔMを次回判断へ戻す。

この段階で初めて、OpenAyaneは「今回の出力を評価する仕組み」から、「意味変化の履歴を通じて判断条件を更新する機構」へ近づく。

Phase 2の中心は、RDEを賢くすることだけではない。RDEの評価結果を、OpenAyaneの関係的制御ループに流し込むことである。
