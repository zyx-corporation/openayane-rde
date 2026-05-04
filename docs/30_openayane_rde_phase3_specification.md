---
title: "OpenAyane RDE Phase 3 詳細仕様書"
version: "0.1-draft"
date: "2026-05-04"
author: "Tomoyuki Kano"
status: "phase 3 specification"
---

# OpenAyane RDE Phase 3 詳細仕様書

## 0. 文書情報

文書名：OpenAyane RDE Phase 3 詳細仕様書  
副題：Agent Execution Gate / Safe Execution Runtime / Human Review Workflow の統合設計  
版：0.1-draft  
作成日：2026-05-04  
作成者：Tomoyuki Kano  
対象リポジトリ：`git@github.com:zyx-corporation/openayane-rde.git`  
前提フェーズ：Phase 1 Structural RDE MVP、Phase 2 Semantic ΔM and Relation Feedback

## 1. Phase 3の位置づけ

Phase 3は、OpenAyane RDEを「文書・コード差分の評価器」から「Agent実行を制御する意味変化ゲート」へ拡張する段階である。

Phase 1では、TaskContract、GeneratorOutput、StructuralDiff、SemanticDelta stub、RDEResult、PolicyDecision、AuditEventを束ねる `Phase1EvaluationResult` を成立させた。Phase 2では、その評価結果をRelationStoreへ戻し、履歴、drift pattern、trust、stability、context_affinityを次回判断へ反映する履歴参照ループを導入した。

Phase 3では、この評価・履歴・Policyのループを、Agentのtool call、外部副作用、workspace変更、実行結果、rollback可能性、人間レビューへ接続する。

```text
Phase 1:
  生成結果と差分を評価する

Phase 2:
  評価履歴をRelationStoreへ戻す

Phase 3:
  評価と履歴を使ってAgent実行を許可・停止・保留・復旧する
```

Phase 3の核心は、Agentの能力を増やすことではない。Agentが実行する前に、何が起きようとしているのかをTaskContract化し、RDEにより意味変化ΔMと副作用リスクを分類し、Policyにより実行可否を決め、必要なら人間レビューまたはrollbackへ接続することである。

## 2. 設計対象

Phase 3では、以下を設計対象とする。

```text
- Human Review Workflow
- SQLiteRelationStore
- Agent Execution Gate
- Safe Execution Runtime
- Tool call gating
- Rollback Manager
- Optional Semantic Evaluator
```

各要素の責務は明確に分離する。

```text
RDE:
  意味変化ΔM、逸脱、危険な副作用の可能性を評価する

Policy:
  RDE結果、RelationContext、実行リスク、制度条件から実行判断を下す

Execution Gate:
  実行前にtool callを遮断・保留・許可する

Safe Execution Runtime:
  実行環境を制限し、dry-run、timeout、resource limit、結果取得を担う

Rollback Manager:
  実行前snapshotとrollback planに基づいて復旧可能性を管理する

Human Review Workflow:
  自動判断できない実行を人間承認へ回す

SQLiteRelationStore:
  Phase 2の履歴状態を永続・検索可能な実装へ拡張する

Optional Semantic Evaluator:
  非同期または高リスク時に意味評価を補助する
```

## 3. Phase 3の目的

Phase 3の目的は、OpenAyane RDEをAgent実行制御へ接続し、以下を実現することである。

```text
1. Agentのtool callをExecutionTaskContractへ変換する
2. tool call実行前にRDE / Policy / RelationContextで評価する
3. 高リスク実行を自動停止またはHuman Reviewへ送る
4. Safe Execution Runtimeで副作用を制限する
5. 実行前snapshotとrollback planを保存する
6. 実行後にPostExecutionDiffを生成し、RDEで再評価する
7. 実行結果をAuditLogとSQLiteRelationStoreへ記録する
8. rollback可能な失敗を自動または人間承認付きで復旧する
9. Optional Semantic Evaluatorを高リスク・曖昧ケースに限定して使用する
10. 実行制御の全判断を監査可能にする
```

## 4. Phase 3の非目的

Phase 3は、自律Agent基盤の完全実装ではない。

以下はPhase 3の非目的である。

```text
- 任意の外部サービスに対する完全なtool実行互換性
- 完全なOS sandboxの実装
- PoP-UIDを含む制度層の完全統合
- 暗号学的に完全な改ざん耐性AuditLog
- LLM evaluator ensembleの本格運用
- 自律Agentの長期計画生成
- すべての副作用に対する完全なrollback保証
- OpenClawまたは他Agent Runtimeへの完全統合
```

Phase 3では、実装可能な最小実行制御として、file operation、shell command dry-run、repository patch、限定tool callを主対象にする。

## 5. 基本原則

### 5.1 実行は評価より後に置く

Agentの実行は、RDE評価とPolicyDecisionの後にのみ許可される。

```text
ToolCallRequest
  ↓
ExecutionTaskContract
  ↓
PreExecution RDE
  ↓
PolicyDecision
  ↓
Execution Gate
  ↓
Safe Execution Runtime
```

実行要求がTaskContract化できない場合は、原則として `human_review` または `halt` とする。

### 5.2 RDEは実行しない

RDEは実行器ではない。RDEは、実行予定内容または実行後結果の意味変化を分類する。

```text
RDEが行う:
  - ΔM分類
  - forbidden side effect検出
  - protected resource変更検出
  - self-report mismatch検出
  - critical corruption判定

RDEが行わない:
  - tool実行
  - file write
  - rollback実行
  - human approvalの代行
  - 外部API呼び出し
```

### 5.3 Policyは実行判断を担う

PolicyはRDE結果を、実行可否へ変換する。

```text
RDE classification:
  preserved / authorized_deviation / inferred_extension / suspicious_drift / critical_corruption

Policy action:
  approve / approve_with_notes / dry_run_only / human_review / halt / rollback_required
```

この分離により、RDE分類の純度を保ちつつ、運用上の実行判断を柔軟に拡張できる。

### 5.4 副作用は明示されなければならない

Agent tool callは、期待される副作用、許可された副作用、禁止された副作用を持つ。

```text
expected_side_effects:
  Agentが意図している変更

allowed_side_effects:
  ユーザーまたはTaskContractが許可した変更

forbidden_side_effects:
  起きてはならない変更
```

`expected_side_effects` が `allowed_side_effects` に含まれない場合、自動実行してはならない。

### 5.5 Rollback可能性は承認判断に影響する

同じ操作でも、rollback可能な場合とrollback不能な場合ではPolicy判断が異なる。

```text
rollback_possible = true:
  medium risk操作をdry_runまたはapproval付き実行へ進められる

rollback_possible = false:
  high risk操作はhuman_review以上を要求する
```

ただし、rollback可能性は安全性そのものではない。rollback planが存在しても、不可逆な外部送信、公開、削除、課金、通知、法的効果を持つ操作は高リスクとして扱う。

## 6. Phase 3全体フロー

### 6.1 実行前フロー

```text
Agent Plan / ToolCallRequest
  ↓
ToolCallNormalizer
  ↓
ExecutionTaskContractBuilder
  ↓
RelationContextLoader
  ↓
PreExecutionRDE
  ↓
ExecutionPolicyBridge
  ↓
ExecutionGateDecision
  ├─ approve → SafeExecutionRuntime
  ├─ dry_run_only → SafeExecutionRuntime(dry_run=True)
  ├─ human_review → HumanReviewQueue
  └─ halt → AuditLog only
```

### 6.2 実行後フロー

```text
SafeExecutionRuntime
  ↓
ExecutionResult
  ↓
PostExecutionDiff
  ↓
PostExecutionRDE
  ↓
ExecutionPolicyBridge
  ↓
AuditLog
  ↓
SQLiteRelationStore Update
  ↓
RollbackManager if needed
```

### 6.3 Human Reviewフロー

```text
human_review decision
  ↓
ReviewRequest
  ↓
ReviewerDecision
  ├─ approve → SafeExecutionRuntime
  ├─ approve_dry_run → SafeExecutionRuntime(dry_run=True)
  ├─ request_revision → Agent revision request
  ├─ reject → halt
  └─ require_rollback_plan → RollbackManager plan validation
```

## 7. 成果物一覧

Phase 3で作成・更新する成果物は以下である。

```text
src/openayane_rde/core/models.py
  - ExecutionTaskContract
  - ToolCallRequest
  - ToolCallRisk
  - ExecutionGateDecision
  - ExecutionResult
  - PostExecutionDiff
  - RollbackPlan
  - RollbackResult
  - ReviewRequest
  - ReviewDecision
  - SemanticEvaluationRequest
  - SemanticEvaluationResult

src/openayane_rde/relation/sqlite_store.py
  - SQLiteRelationStore
  - schema initialization
  - transaction handling
  - migration support minimal

src/openayane_rde/agent/tool_contract.py
  - build_execution_task_contract
  - normalize_tool_call
  - infer_side_effects

src/openayane_rde/agent/execution_gate.py
  - evaluate_before_execution
  - decide_execution_gate
  - enforce_execution_decision

src/openayane_rde/runtime/safe_execution.py
  - SafeExecutionRuntime
  - dry-run interface
  - timeout
  - resource limit
  - working directory isolation

src/openayane_rde/runtime/result.py
  - ExecutionResult serialization
  - stdout / stderr / changed_resources

src/openayane_rde/runtime/rollback.py
  - RollbackManager
  - snapshot creation
  - rollback plan validation
  - rollback execution

src/openayane_rde/review/workflow.py
  - HumanReviewWorkflow
  - ReviewQueue interface
  - in-memory implementation

src/openayane_rde/review/models.py
  - ReviewRequest
  - ReviewDecision

src/openayane_rde/semantic/evaluator.py
  - SemanticEvaluator Protocol
  - RuleBasedSemanticEvaluator
  - LLM evaluator adapter stub

src/openayane_rde/policy/execution_rules.py
  - execution risk rules
  - side effect rules
  - rollback-aware policy adjustment

src/openayane_rde/audit/log.py
  - Execution audit event support

tests/unit/test_sqlite_relation_store.py
tests/unit/test_tool_contract_builder.py
tests/unit/test_execution_gate.py
tests/unit/test_safe_execution_runtime.py
tests/unit/test_rollback_manager.py
tests/unit/test_human_review_workflow.py
tests/unit/test_optional_semantic_evaluator.py
tests/integration/test_agent_execution_gate_flow.py
tests/integration/test_execution_rollback_flow.py
```

## 8. データモデル

### 8.1 ToolCallRequest

Agentからのtool call要求を正規化した入力モデルである。

```python
class ToolCallRequest(BaseModel):
    tool_call_id: str
    agent_id: str
    tool_name: str
    action_name: str
    arguments: dict[str, Any]
    target_resources: list[str] = Field(default_factory=list)
    declared_purpose: str | None = None
    agent_self_report: str | None = None
    created_at: datetime
```

要件：

```text
- tool_call_idは監査単位として一意である
- argumentsはそのまま実行せず、必ず正規化する
- target_resourcesが空の場合、ToolCallNormalizerが推定を試みる
- 推定不能な場合はunknown targetとしてhuman_reviewへ送る
```

### 8.2 ExecutionTaskContract

tool callをRDE評価可能な契約へ変換したモデルである。

```python
class ExecutionTaskContract(BaseModel):
    contract_id: str
    source_tool_call_id: str
    agent_id: str
    action_type: Literal[
        "read",
        "write",
        "delete",
        "execute",
        "network",
        "external_api",
        "repository_patch",
        "unknown",
    ]
    tool_name: str
    target_resources: list[str]
    expected_side_effects: list[str]
    allowed_side_effects: list[str]
    forbidden_side_effects: list[str]
    protected_resources: list[str]
    rollback_strategy: Literal[
        "none",
        "file_snapshot",
        "git_patch_reverse",
        "transactional",
        "manual",
    ]
    rollback_required: bool = False
    required_user_approval: bool = False
    max_runtime_ms: int | None = None
    max_output_bytes: int | None = None
    network_allowed: bool = False
    created_at: datetime
```

`ExecutionTaskContract` は、通常の `TaskContract` と完全に同一ではない。通常のTaskContractが文書・コード変換の意味差分を扱うのに対し、ExecutionTaskContractは副作用を含む実行契約を扱う。

### 8.3 ToolCallRisk

```python
class ToolCallRisk(BaseModel):
    risk_level: Literal["low", "medium", "high", "critical"]
    risk_score: float = Field(ge=0.0, le=1.0)
    irreversible: bool = False
    external_side_effect: bool = False
    protected_resource_touched: bool = False
    rollback_possible: bool = False
    unknown_target: bool = False
    reasons: list[str] = Field(default_factory=list)
```

初期リスク規則：

```text
read only + known local target:
  low

write to non-protected local file + rollback possible:
  medium

delete / overwrite protected resource:
  high or critical

network / external_api / notification / publishing:
  high

unknown target / unknown side effect:
  high

credential / secret / key material access:
  critical

irreversible external side effect:
  critical unless explicit human approval exists
```

### 8.4 ExecutionGateDecision

```python
class ExecutionGateDecision(BaseModel):
    decision_id: str
    contract_id: str
    policy_action: Literal[
        "approve",
        "approve_with_notes",
        "dry_run_only",
        "human_review",
        "halt",
    ]
    reason: str
    risk: ToolCallRisk
    rde_result: RDEResult | None = None
    relation_context: RelationContext | None = None
    rollback_plan_required: bool = False
    review_request_id: str | None = None
    audit_event_id: str | None = None
    created_at: datetime
```

### 8.5 ExecutionResult

```python
class ExecutionResult(BaseModel):
    execution_id: str
    contract_id: str
    tool_call_id: str
    status: Literal[
        "not_executed",
        "dry_run_completed",
        "completed",
        "failed",
        "timed_out",
        "blocked",
    ]
    exit_code: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    changed_resources: list[str] = Field(default_factory=list)
    observed_side_effects: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    rollback_plan_id: str | None = None
    error_message: str | None = None
```

要件：

```text
- stdout / stderrはmax_output_bytesで切り詰め可能にする
- changed_resourcesは実行後diffまたはruntime adapterから取得する
- failed / timed_outの場合もAuditEventを残す
- not_executed / blockedも実行結果として記録する
```

### 8.6 PostExecutionDiff

```python
class PostExecutionDiff(BaseModel):
    diff_id: str
    contract_id: str
    before_snapshot_id: str | None = None
    after_snapshot_id: str | None = None
    changed_resources: list[str]
    unexpected_side_effects: list[str]
    protected_resource_changes: list[str]
    structural_diff: StructuralDiff | None = None
    semantic_delta: SemanticDelta | None = None
    created_at: datetime
```

PostExecutionDiffは、実行が意図通りだったかをRDEで再評価するために使う。

### 8.7 RollbackPlan

```python
class RollbackPlan(BaseModel):
    rollback_plan_id: str
    contract_id: str
    strategy: Literal[
        "none",
        "file_snapshot",
        "git_patch_reverse",
        "transactional",
        "manual",
    ]
    target_resources: list[str]
    snapshot_refs: list[str] = Field(default_factory=list)
    reverse_patch_path: str | None = None
    manual_steps: list[str] = Field(default_factory=list)
    validated: bool = False
    validation_message: str | None = None
    created_at: datetime
```

### 8.8 RollbackResult

```python
class RollbackResult(BaseModel):
    rollback_result_id: str
    rollback_plan_id: str
    status: Literal[
        "not_required",
        "completed",
        "failed",
        "manual_required",
        "not_possible",
    ]
    restored_resources: list[str] = Field(default_factory=list)
    error_message: str | None = None
    audit_event_id: str | None = None
    completed_at: datetime | None = None
```

### 8.9 ReviewRequest / ReviewDecision

```python
class ReviewRequest(BaseModel):
    review_request_id: str
    contract_id: str
    tool_call_id: str
    agent_id: str
    reason: str
    risk: ToolCallRisk
    proposed_action_summary: str
    expected_side_effects: list[str]
    forbidden_side_effects: list[str]
    rollback_plan: RollbackPlan | None = None
    rde_result: RDEResult | None = None
    relation_context: RelationContext | None = None
    status: Literal["pending", "approved", "rejected", "revision_requested", "expired"] = "pending"
    created_at: datetime
```

```python
class ReviewDecision(BaseModel):
    review_decision_id: str
    review_request_id: str
    reviewer_id: str
    decision: Literal[
        "approve",
        "approve_dry_run",
        "reject",
        "request_revision",
        "require_rollback_plan",
    ]
    reason: str
    approved_at: datetime | None = None
```

## 9. SQLiteRelationStore

### 9.1 目的

Phase 2ではJSONまたはSQLiteを選択可能としていた。Phase 3では、Agent実行履歴、Review、ExecutionResult、Rollbackを扱うため、SQLiteRelationStoreを正式な永続層として設計する。

SQLiteRelationStoreは、RelationStateだけでなく、実行判断と監査イベントへの参照を保持する。ただし、AuditLogそのものの完全代替にはしない。

```text
AuditLog:
  起きたことの時系列記録

SQLiteRelationStore:
  監査結果から計算された関係状態と検索可能な索引
```

### 9.2 ファイル配置

```text
.relation_store/openayane_relation.sqlite3
```

設定で変更可能にする。

```toml
[relation_store]
type = "sqlite"
path = ".relation_store/openayane_relation.sqlite3"
```

### 9.3 テーブル構成

```sql
CREATE TABLE IF NOT EXISTS relation_records (
  relation_id TEXT PRIMARY KEY,
  subject_id TEXT NOT NULL,
  object_id TEXT NOT NULL,
  relation_type TEXT NOT NULL,
  trust REAL NOT NULL,
  stability REAL NOT NULL,
  context_affinity REAL NOT NULL,
  interaction_count INTEGER NOT NULL,
  critical_corruption_count INTEGER NOT NULL,
  suspicious_drift_count INTEGER NOT NULL,
  self_report_mismatch_count INTEGER NOT NULL,
  review_threshold_adjustment REAL NOT NULL,
  last_delta_m REAL NOT NULL,
  last_audit_event_id TEXT,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(subject_id, object_id, relation_type)
);
```

```sql
CREATE TABLE IF NOT EXISTS drift_patterns (
  pattern_id TEXT PRIMARY KEY,
  relation_id TEXT NOT NULL,
  kind TEXT NOT NULL,
  count INTEGER NOT NULL,
  severity TEXT NOT NULL,
  examples_json TEXT NOT NULL DEFAULT '[]',
  last_seen_at TEXT NOT NULL,
  FOREIGN KEY(relation_id) REFERENCES relation_records(relation_id)
);
```

```sql
CREATE TABLE IF NOT EXISTS execution_events (
  execution_event_id TEXT PRIMARY KEY,
  contract_id TEXT NOT NULL,
  tool_call_id TEXT NOT NULL,
  agent_id TEXT NOT NULL,
  tool_name TEXT NOT NULL,
  action_type TEXT NOT NULL,
  gate_action TEXT NOT NULL,
  risk_level TEXT NOT NULL,
  status TEXT NOT NULL,
  audit_event_id TEXT,
  rollback_plan_id TEXT,
  review_request_id TEXT,
  created_at TEXT NOT NULL,
  metadata_json TEXT NOT NULL DEFAULT '{}'
);
```

```sql
CREATE TABLE IF NOT EXISTS review_requests (
  review_request_id TEXT PRIMARY KEY,
  contract_id TEXT NOT NULL,
  tool_call_id TEXT NOT NULL,
  agent_id TEXT NOT NULL,
  status TEXT NOT NULL,
  reason TEXT NOT NULL,
  risk_json TEXT NOT NULL,
  rollback_plan_json TEXT,
  rde_result_json TEXT,
  relation_context_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

```sql
CREATE TABLE IF NOT EXISTS review_decisions (
  review_decision_id TEXT PRIMARY KEY,
  review_request_id TEXT NOT NULL,
  reviewer_id TEXT NOT NULL,
  decision TEXT NOT NULL,
  reason TEXT NOT NULL,
  approved_at TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(review_request_id) REFERENCES review_requests(review_request_id)
);
```

```sql
CREATE TABLE IF NOT EXISTS rollback_plans (
  rollback_plan_id TEXT PRIMARY KEY,
  contract_id TEXT NOT NULL,
  strategy TEXT NOT NULL,
  target_resources_json TEXT NOT NULL,
  snapshot_refs_json TEXT NOT NULL DEFAULT '[]',
  reverse_patch_path TEXT,
  manual_steps_json TEXT NOT NULL DEFAULT '[]',
  validated INTEGER NOT NULL DEFAULT 0,
  validation_message TEXT,
  created_at TEXT NOT NULL
);
```

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
  version INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  applied_at TEXT NOT NULL
);
```

### 9.4 Index

```sql
CREATE INDEX IF NOT EXISTS idx_relation_subject_object
  ON relation_records(subject_id, object_id);

CREATE INDEX IF NOT EXISTS idx_drift_relation_kind
  ON drift_patterns(relation_id, kind);

CREATE INDEX IF NOT EXISTS idx_execution_contract
  ON execution_events(contract_id);

CREATE INDEX IF NOT EXISTS idx_execution_tool_call
  ON execution_events(tool_call_id);

CREATE INDEX IF NOT EXISTS idx_review_status
  ON review_requests(status);
```

### 9.5 SQLiteRelationStore API

```python
class SQLiteRelationStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def initialize(self) -> None:
        ...

    def get(self, subject_id: str, object_id: str, relation_type: str) -> RelationStoreRecord | None:
        ...

    def upsert(self, record: RelationStoreRecord) -> None:
        ...

    def load_context(self, subject_id: str, object_id: str, relation_type: str) -> RelationContext:
        ...

    def append_execution_event(self, event: ExecutionResult | ExecutionGateDecision) -> None:
        ...

    def create_review_request(self, request: ReviewRequest) -> None:
        ...

    def update_review_request_status(self, request_id: str, status: str) -> None:
        ...

    def append_review_decision(self, decision: ReviewDecision) -> None:
        ...

    def save_rollback_plan(self, plan: RollbackPlan) -> None:
        ...
```

### 9.6 トランザクション方針

以下は単一トランザクションで行う。

```text
- relation_records更新 + drift_patterns更新
- review_request作成 + execution_event記録
- review_decision記録 + review_request status更新
- rollback_plan保存 + execution_event更新
```

SQLiteの同時書き込み制約を考慮し、Phase 3では単一プロセス・単一writerを前提にする。将来的な複数Agent同時実行では、write queueまたはservice化を検討する。

## 10. Agent Execution Gate

### 10.1 目的

Agent Execution Gateは、Agentのtool callを実行前に評価し、実行を許可、dry-run限定、人間レビュー、停止へ振り分ける。

### 10.2 API

```python
def evaluate_before_execution(
    tool_call: ToolCallRequest,
    relation_store: RelationStore,
    policy_config: ExecutionPolicyConfig,
) -> ExecutionGateDecision:
    ...
```

```python
def enforce_execution_decision(
    decision: ExecutionGateDecision,
    runtime: SafeExecutionRuntime,
    review_workflow: HumanReviewWorkflow,
) -> ExecutionResult | ReviewRequest:
    ...
```

### 10.3 判定規則

```text
RDE critical_corruption:
  halt

ToolCallRisk critical:
  halt or human_review if explicitly configured

ToolCallRisk high + rollback_possible false:
  human_review

ToolCallRisk high + external_side_effect true:
  human_review

ToolCallRisk medium + trust < 0.4:
  human_review

ToolCallRisk medium + rollback_possible true:
  dry_run_only or approve_with_notes

ToolCallRisk low + trust >= 0.5:
  approve

unknown target:
  human_review

protected resource touched:
  human_review or halt depending on policy
```

### 10.4 PolicyConfig

```python
class ExecutionPolicyConfig(BaseModel):
    allow_auto_execute_low_risk: bool = True
    allow_auto_execute_medium_risk: bool = False
    require_review_for_external_side_effects: bool = True
    require_review_for_protected_resources: bool = True
    halt_on_critical_risk: bool = True
    allow_dry_run_for_high_risk: bool = True
    min_trust_for_auto_execute: float = 0.5
    min_stability_for_auto_execute: float = 0.4
```

### 10.5 受け入れ基準

```text
- low risk read operationはapproveされる
- protected file writeはhuman_reviewへ送られる
- secret accessはhaltされる
- unknown targetはhuman_reviewへ送られる
- low trust agentのmedium risk writeはhuman_reviewへ送られる
- rollback不能な外部API操作はhuman_reviewまたはhaltになる
```

## 11. Tool call gating

### 11.1 目的

Tool call gatingは、tool callの種類ごとに、副作用、危険度、rollback可能性を判定する。

### 11.2 Tool分類

```text
read_local_file:
  action_type = read
  default risk = low
  rollback = none

write_local_file:
  action_type = write
  default risk = medium
  rollback = file_snapshot

delete_local_file:
  action_type = delete
  default risk = high
  rollback = file_snapshot if possible

shell_command:
  action_type = execute
  default risk = high
  rollback = manual or none

network_request:
  action_type = network
  default risk = high
  rollback = none

external_api_call:
  action_type = external_api
  default risk = high
  rollback = manual or none

git_patch:
  action_type = repository_patch
  default risk = medium
  rollback = git_patch_reverse
```

### 11.3 危険語・危険操作の初期規則

shell commandは特に保守的に扱う。

```text
critical:
  rm -rf /
  sudo rm
  chmod -R 777
  curl ... | sh
  wget ... | sh
  secret / token / private_keyへのアクセス
  git push --force
  destructive database migration

high:
  rm / delete
  mv overwrite
  network write
  package install
  system config modification

medium:
  local file write
  git apply
  formatting
  test execution with file outputs

low:
  read-only listing
  cat / grep / rg
  pytest without write side effect
```

### 11.4 target_resources推定

ToolCallNormalizerは、argumentsからtarget_resourcesを推定する。

```text
path / file / filename / cwd:
  local resourceとして推定

url / endpoint:
  external resourceとして推定

command:
  parserで対象パスを推定。不明ならunknown target
```

推定不能なwrite / delete / executeはhuman_reviewへ送る。

## 12. Safe Execution Runtime

### 12.1 目的

Safe Execution Runtimeは、許可されたtool callを制限付きで実行し、結果と副作用を記録する。

Phase 3では、完全なOS sandboxではなく、アプリケーションレベルの安全制御を実装する。

### 12.2 API

```python
class SafeExecutionRuntime:
    def execute(
        self,
        contract: ExecutionTaskContract,
        tool_call: ToolCallRequest,
        rollback_plan: RollbackPlan | None = None,
        dry_run: bool = False,
    ) -> ExecutionResult:
        ...
```

### 12.3 実行制約

```text
- max_runtime_msを超えた場合timed_out
- max_output_bytesを超えたstdout/stderrはtruncate
- network_allowed=falseの場合、network toolは実行不可
- protected_resourcesはruntime側でも二重チェック
- dry_runの場合、実副作用を起こさない
- 実行前にrollback snapshotを作成する
```

### 12.4 dry-runの扱い

dry-runはtoolごとに意味が異なる。

```text
file write:
  書き込み予定内容とdiffを生成するが保存しない

git patch:
  git apply --check相当

shell command:
  原則として実行しない。安全なread-only commandのみsimulateまたは実行可

external_api:
  実送信しない。request payloadを検証するのみ
```

### 12.5 受け入れ基準

```text
- dry_run=Trueではファイルが変更されない
- timeout時にExecutionResult.status = timed_outになる
- max_output_bytesを超える出力が切り詰められる
- network_allowed=falseでnetwork toolがblockedになる
- protected resource変更はruntime側でもblockedになる
```

## 13. Rollback Manager

### 13.1 目的

Rollback Managerは、実行前の復旧可能性を評価し、snapshotまたはreverse patchを保存し、必要時に復旧を実行する。

### 13.2 API

```python
class RollbackManager:
    def create_plan(self, contract: ExecutionTaskContract) -> RollbackPlan:
        ...

    def validate_plan(self, plan: RollbackPlan) -> RollbackPlan:
        ...

    def execute_rollback(self, plan: RollbackPlan) -> RollbackResult:
        ...
```

### 13.3 strategy別仕様

```text
none:
  rollback不可。high以上のriskではhuman_reviewを要求する

file_snapshot:
  実行前に対象ファイルをsnapshot directoryへコピーする

git_patch_reverse:
  git diffからreverse patchを生成する

transactional:
  tool adapterがtransactionを提供する場合のみ使用

manual:
  自動復旧せず、manual_stepsを記録する
```

### 13.4 snapshot配置

```text
.relation_store/rollback/
  snapshots/
    {rollback_plan_id}/
  patches/
    {rollback_plan_id}.patch
```

### 13.5 rollback_required条件

```text
- protected_resourcesを変更する
- delete / overwriteを含む
- high risk以上
- PolicyConfigでrollback_requiredが指定されている
- Human Reviewでrequire_rollback_planが返された
```

### 13.6 受け入れ基準

```text
- file write前にsnapshotが作成される
- rollback実行で変更前状態へ戻せる
- rollback不能操作ではvalidated=falseになる
- manual strategyではmanual_stepsが記録される
- rollback失敗時もAuditEventが残る
```

## 14. Human Review Workflow

### 14.1 目的

Human Review Workflowは、自動実行できないtool callを人間承認へ回す。

Phase 3では、最小実装としてInMemoryReviewQueueとSQLite永続化を提供する。

### 14.2 API

```python
class HumanReviewWorkflow:
    def create_request(self, decision: ExecutionGateDecision, contract: ExecutionTaskContract) -> ReviewRequest:
        ...

    def submit_decision(self, decision: ReviewDecision) -> ReviewRequest:
        ...

    def get_pending(self) -> list[ReviewRequest]:
        ...

    def get(self, review_request_id: str) -> ReviewRequest | None:
        ...
```

### 14.3 Review UI非依存

Phase 3ではUIは実装しない。CLIまたはAPIからReviewRequestを取得し、ReviewDecisionを投入できる構造にする。

```text
openayane review list
openayane review show <review_request_id>
openayane review approve <review_request_id>
openayane review reject <review_request_id>
```

CLI実装はPhase 5でもよいが、Workflow APIはPhase 3で定義する。

### 14.4 Review判断

```text
approve:
  実行を許可する

approve_dry_run:
  dry-runのみ許可する

reject:
  実行しない

request_revision:
  Agentへ計画修正を要求する

require_rollback_plan:
  rollback plan作成後に再レビューする
```

### 14.5 受け入れ基準

```text
- human_review判断からReviewRequestが作成される
- pending requestを一覧できる
- approveにより実行へ進められる
- rejectによりExecutionResult.status = blockedになる
- require_rollback_planでRollbackPlan作成を要求できる
- review decisionがSQLiteRelationStoreに保存される
```

## 15. Optional Semantic Evaluator

### 15.1 目的

Optional Semantic Evaluatorは、構造差分だけでは判断しにくい意味変化を補助評価する。

ただし、Phase 3でもRDEをLLM evaluatorそのものに還元しない。Semantic Evaluatorは補助器であり、RDE分類の唯一根拠ではない。

### 15.2 使用条件

```text
- ToolCallRisk high以上
- structural diffは小さいが意味変化が疑われる
- self_reportと実差分が矛盾する
- allowed_side_effectsとの照合が曖昧
- human_review前に補足説明が必要
```

### 15.3 Protocol

```python
class SemanticEvaluator(Protocol):
    def evaluate_execution_intent(
        self,
        contract: ExecutionTaskContract,
        tool_call: ToolCallRequest,
        relation_context: RelationContext | None = None,
    ) -> SemanticEvaluationResult:
        ...

    def evaluate_post_execution(
        self,
        contract: ExecutionTaskContract,
        result: ExecutionResult,
        post_diff: PostExecutionDiff,
    ) -> SemanticEvaluationResult:
        ...
```

### 15.4 SemanticEvaluationResult

```python
class SemanticEvaluationResult(BaseModel):
    evaluation_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    suspected_delta_m: list[str]
    preserved_elements: list[str]
    transformed_elements: list[str]
    inferred_extensions: list[str]
    unresolved_elements: list[str]
    drift_risks: list[str]
    recommendation: Literal[
        "no_issue",
        "approve_with_notes",
        "human_review",
        "halt",
    ]
    explanation: str
    created_at: datetime
```

### 15.5 初期実装

Phase 3初期では、RuleBasedSemanticEvaluatorを実装する。

```text
- forbidden_side_effectsとexpected_side_effectsの重なりを検出
- declared_purposeとaction_typeの不一致を検出
- protected_resource変更の説明不足を検出
- external_side_effectの自己申告欠落を検出
```

LLM adapterはstubでよい。

## 16. AuditLog拡張

### 16.1 追加イベント種別

```text
execution_gate_evaluated
execution_blocked
execution_approved
execution_dry_run_completed
execution_completed
execution_failed
execution_timed_out
human_review_requested
human_review_decided
rollback_plan_created
rollback_completed
rollback_failed
semantic_evaluation_completed
```

### 16.2 AuditEvent payload

Execution関連AuditEventには以下を含める。

```text
- tool_call_id
- contract_id
- agent_id
- tool_name
- action_type
- gate_decision
- risk_level
- rde_classification
- policy_action
- review_request_id optional
- rollback_plan_id optional
- execution_id optional
- relation_id optional
```

### 16.3 受け入れ基準

```text
- blockedされたtool callもAuditLogに残る
- human review request / decisionがAuditLogに残る
- rollback plan / resultがAuditLogに残る
- execution resultとaudit_event_idが相互参照できる
```

## 17. 実装順序

Phase 3の推奨実装順序は以下である。

```text
1. core models追加
2. SQLiteRelationStore schema / initialize実装
3. SQLiteRelationStore get / upsert / load_context実装
4. ToolCallRequest / ExecutionTaskContract builder実装
5. ToolCallRisk scoring実装
6. ExecutionPolicyConfig / execution_rules実装
7. Agent Execution Gate実装
8. SafeExecutionRuntime dry-run最小実装
9. RollbackManager file_snapshot実装
10. HumanReviewWorkflow InMemory実装
11. HumanReviewWorkflow SQLite永続化
12. PostExecutionDiff生成
13. PostExecutionRDE接続
14. AuditLog拡張
15. Optional Semantic Evaluator rule-based実装
16. integration tests追加
17. schema export / fixture validation更新
18. CI更新
```

## 18. テスト方針

### 18.1 Unit Tests

```text
test_sqlite_relation_store.py:
  - initialize creates tables
  - upsert relation record
  - load relation context
  - transaction rollback on error

 test_tool_contract_builder.py:
  - read tool call to low risk contract
  - write tool call to medium risk contract
  - unknown target becomes high risk
  - external API becomes high risk

 test_execution_gate.py:
  - low risk approve
  - protected resource human_review
  - critical secret access halt
  - low trust medium risk human_review

 test_safe_execution_runtime.py:
  - dry-run does not modify file
  - timeout handled
  - output truncation
  - network disallowed blocks network action

 test_rollback_manager.py:
  - file snapshot created
  - rollback restores file
  - no rollback strategy validation fails

 test_human_review_workflow.py:
  - create pending review request
  - approve request
  - reject request
  - require rollback plan

 test_optional_semantic_evaluator.py:
  - purpose/action mismatch detected
  - forbidden side effect detected
  - protected resource explanation missing detected
```

### 18.2 Integration Tests

```text
test_agent_execution_gate_flow.py:
  ToolCallRequest
    → ExecutionTaskContract
    → PreExecution RDE
    → ExecutionGateDecision
    → SafeExecutionRuntime
    → ExecutionResult
    → AuditLog
    → SQLiteRelationStore

 test_execution_rollback_flow.py:
  write file
    → snapshot
    → execute
    → post diff suspicious
    → rollback
    → rollback result audited

 test_human_review_execution_flow.py:
  high risk tool call
    → human_review
    → review approve_dry_run
    → dry-run execution
    → audit
```

### 18.3 Golden Tests

Golden fixtureには以下を含める。

```text
fixtures/phase3/tool_calls/read_file_low_risk.json
fixtures/phase3/tool_calls/write_file_medium_risk.json
fixtures/phase3/tool_calls/delete_protected_high_risk.json
fixtures/phase3/tool_calls/external_api_high_risk.json
fixtures/phase3/tool_calls/secret_access_critical.json
fixtures/phase3/review/high_risk_review_request.json
fixtures/phase3/rollback/file_snapshot_plan.json
```

## 19. 受け入れ基準

Phase 3は、以下を満たした時点で完了とする。

```text
1. ToolCallRequestをExecutionTaskContractへ変換できる
2. tool callのriskをlow / medium / high / criticalへ分類できる
3. Agent Execution Gateがapprove / dry_run_only / human_review / haltを返せる
4. protected resource変更を自動実行前に停止またはreviewへ送れる
5. SafeExecutionRuntimeがdry-run / timeout / output limitを持つ
6. file_snapshot rollback planを生成できる
7. rollbackにより単純なfile writeを復旧できる
8. HumanReviewWorkflowでpending / approve / reject / require_rollback_planを扱える
9. SQLiteRelationStoreがRelationState、ExecutionEvent、ReviewRequest、RollbackPlanを保存できる
10. 実行前判断、実行結果、review、rollbackがAuditLogへ記録される
11. PostExecutionDiffを生成し、実行後RDE評価へ渡せる
12. Optional Semantic Evaluatorがrule-based補助評価を返せる
13. Phase 3 integration testsがCIで通る
```

## 20. 逸脱リスクと対策

### 20.1 RDEが実行器へ膨張するリスク

リスク：RDE Coreがtool実行やrollbackを直接扱い始める。  
対策：RDEは分類のみを返し、実行はExecutionRuntime、復旧はRollbackManagerへ分離する。

### 20.2 Rollback可能性を安全性と誤認するリスク

リスク：rollback planがあるため高リスク実行を安易に許可する。  
対策：external side effect、credential access、公開、通知、課金、削除はrollback可能性に関係なく高リスク以上にする。

### 20.3 Human Reviewが形骸化するリスク

リスク：review requestに判断材料が不足し、人間が実質的に承認ボタンを押すだけになる。  
対策：ReviewRequestにexpected / forbidden side effects、risk reasons、rollback plan、RDE result、relation contextを必ず含める。

### 20.4 SQLiteがAuditLogの代替になるリスク

リスク：検索しやすいSQLiteだけを見て、時系列監査ログが失われる。  
対策：SQLiteRelationStoreは状態と索引であり、AuditLogを一次記録として維持する。

### 20.5 Optional Semantic Evaluatorへの過信

リスク：LLM evaluatorの説明をRDE判断そのものとして扱う。  
対策：Semantic Evaluatorは補助評価とし、RDE分類、Policy判断、AuditLogに根拠を分離して残す。

## 21. Phase 4への接続条件

Phase 4 Institution and Accountability Layerへ進むために、Phase 3完了時点で以下が必要である。

```text
- actor / agent_id / reviewer_id / subject_idが明示されている
- ReviewDecisionに承認者と理由が保存されている
- ExecutionGateDecisionにPolicy根拠が保存されている
- rollback不可操作が識別されている
- protected resourceとauthority ruleを接続できる
- AuditLogから責任連鎖を再構成できる
```

Phase 4では、これをInstitutionRule、Authority、PoP-UID、Accountability mappingへ接続する。

## 22. RDE差異検証メモ

### 22.1 保存された要素

Phase 3仕様は、既存のRDE設計思想を保持している。すなわち、RDEはDiff、Policy、Safety Filter、LLM Evaluatorそのものではなく、意味変化ΔMを分類する評価層である。GeneratorとEvaluatorの分離、TaskContract中心設計、AuditLog先行、RelationStoreによる履歴参照も保存している。

### 22.2 変換された要素

Phase 1 / Phase 2で文書・コード差分を対象としていたRDEを、Agent tool callと実行副作用へ拡張した。ここでの変換は、RDEの理論的主張を広げたものではなく、既存の「意味変化監査」を実行前後の副作用評価へ適用したものである。

### 22.3 補完された要素

Human Review Workflow、SQLiteRelationStore、Safe Execution Runtime、Rollback Manager、Tool call gating、Optional Semantic Evaluatorを、Phase 3の具体的実装単位として補完した。特に、rollback可能性をPolicy判断に使うが安全性と同一視しない点を明示した。

### 22.4 未解決のまま残した要素

完全なOS sandbox、外部Agent Runtimeとの完全統合、暗号学的AuditLog、PoP-UID、Institution Layer、LLM evaluator ensembleはPhase 3では未解決として残す。これらはPhase 4以降またはPhase 5以降の対象である。

### 22.5 逸脱リスク

主な逸脱リスクは、RDEが実行器へ膨張すること、rollback可能性を安全性と誤認すること、Optional Semantic Evaluatorを最終判断者にしてしまうことである。本仕様では、RDE、Policy、ExecutionRuntime、RollbackManager、HumanReviewを分離し、この逸脱を抑制する。

### 22.6 次回更新方針

次回更新では、Phase 3の実装計画を `docs/31_openayane_rde_phase3_implementation_plan.md` として分離し、実装順序、TDD fixture、最小PR分割、CI追加項目、各モジュールの公開APIをさらに具体化する。
