---
title: "OpenAyane RDE Phase 3 production-ready 制約解消計画"
version: "0.4"
date: "2026-05-04"
status: "in_progress"
---

# OpenAyane RDE Phase 3：production-ready 制約解消計画

## 0. 文書情報

文書名：Phase 3「production-ready ではない」制約の解消計画  
対象：`docs/30` Phase 3 仕様、`docs/31` 実装レポート、`docs/32` 評価レポートで明示された限界  
位置づけ：**ロードマップ**（Issue 化・スプリント分割の入力）

### 0.1 実装反映サマリ（コードベース・2026-05 時点）

次を **マージ済み実装** として追う（詳細は `CHANGELOG.md`）。

```text
- API: evaluate_before_execution() → ExecutionGateEvaluation（.decision / .contract）。破壊的変更。
- モデル: RDEResult.evaluation_kind（pre_synthetic | post_structural）、ToolExecutionResult.audit_event_id
- スキーマ: schemas/rde_result.schema.json（evaluation_kind）、docs/audit_event_schema.md ↔ audit_event.schema.json 同期手順
- 監査: openayane_rde.audit.log — audit_event_execution_gate_evaluated 等、append_audit_event
- 実行後 RDE: run_phase1_evaluation_from_post_execution_diff（runtime/_flow.py、post_execution 再エクスポート、パッケージ直下公開）
- レビュー再開: execute_after_review_decision（approve / approve_dry_run）
- SQLite: execution_events.audit_event_id に ToolExecutionResult 側 ID を保存
- テスト: tests/integration/test_post_execution_phase1_connector.py、test_agent_execution_gate_flow.py（approve_dry_run E2E）、
         tests/unit/test_safe_execution_runtime.py（.. 逸脱・symlink）、test_phase3_golden_fixtures.py、fixtures/phase3/*
```

**未着手:** Wave C（C1–C3、および C4 の TOCTOU 等の深堀り）、Wave D 全体、Wave E。Wave C4 のうち **パス traversal / symlink の回帰テスト** は先行実装済み（下記 Wave C 参照）。

関連：

```text
- docs/30_openayane_rde_phase3_specification.md（非目的・逸脱リスク）
- docs/31_openayane_rde_phase3_implementation_report.md（技術的負債一覧）
- docs/32_openayane_rde_phase3_evaluation_report.md（P0–P3 課題）— §8.6 より本書へリンク
- CHANGELOG.md（移行・破壊的変更）
```

## 1. 「production-ready」の定義（段階）

本リポジトリでは **production-ready を単一の boolean として扱わない**。Phase 3 の到達度は、運用シナリオ別の成熟度レベルとして定義する。

| レベル | 呼称 | 目安 |
|--------|------|------|
| L0 | **Lab / MVP** | 単一プロセス・限定ファイル操作・シェル未実行（タイムアウトは近似）。 |
| L1 | **Internal Pilot Ready** | 監査ヘルパ・PostExecution→Phase1・`evaluation_kind`・パス回帰・approve_dry_run E2E まで実装済み。全エントリポイントへの監査組込みと CI 緑の継続は運用で確認。 |
| L2 | **Bounded Production Ready** | allowlist 付き subprocess / 制限付きネットワーク・タイムアウト実効・SQLite 書き込みキューまたは単一 writer サービス化。信頼境界を限定した本番利用。 |
| L3 | **High Assurance** | コンテナ等の隔離、Institution / authority 連携、暗号学的監査は **Phase 4 以降**（仕様非目的の範囲を含む）。 |

**制約解消計画**は主に **L0 → L1** と **L1 → L2** を対象とする。L3 は本計画では **スコープ外** とし、Phase 4 計画へ接続する。

重要なのは、L1 を「本番利用可能」と呼ばないことである。L1 はあくまで **internal-pilot ready** であり、限定された内部利用、監査確認、回帰テスト、レビュー訓練のための段階である。本番という語は、信頼境界、実効 runtime 制御、migration、運用監査が揃う L2 以降に限定する。

## 2. 現状制約の整理（評価レポート対応表）

| 領域 | 制約・リスク | 解消の方向性 |
|------|----------------|--------------|
| **概念** | synthetic RDE と本来の RDE の混同 | **進捗:** `RDEResult.evaluation_kind` と監査 payload。命名整理（別型化）は任意。 |
| **根拠** | RDE分類の根拠が機械可読でない | **追加課題:** `evaluation_kind` に加え、`evidence_basis` を導入する。 |
| **API** | ゲートがタプル返却 | **完了:** `ExecutionGateEvaluation`（`evaluate_before_execution` の戻り値）。 |
| **互換** | `ModificationOutcome` リネーム | **進捗:** `CHANGELOG.md` 記載。README への短い言及は任意。 |
| **Runtime** | シェル・HTTP 未実行、timeout 近似 | **allowlist subprocess**、**プロキシ経由 HTTP**、**実効 timeout（kill）** を段階導入 |
| **Runtime** | network_allowed が粗い | **追加課題:** HTTP実行前に `external_side_effect_kind` を定義する。 |
| **Runtime** | symlink / TOCTOU | **進捗:** `..` 逸脱・ワークスペース外 symlink の回帰テスト。TOCTOU / fd 検証は未。 |
| **Rollback** | file_snapshot 中心 | 多ファイル・delete E2E；**git_patch_reverse** は P2 以降 |
| **永続化** | SQLite 単一 writer | **書き込みキュー**または **RelationStore サービス**（単一プロセス RPC） |
| **永続化** | review 列不足 | **migration v2** で payload 完全保存 |
| **監査** | AuditLog 統合が薄い | **進捗:** execution 系イベントビルダと `append_audit_event`；ゲート／実行結果と `audit_event_id` の対応は **SQLite + モデル**で可。全経路での自動 append は未。 |
| **RDE** | PostExecutionRDE 未配線 | **完了:** `run_phase1_evaluation_from_post_execution_diff`。ただし実行文脈を落とさない集約型の検討余地あり。 |
| **テスト** | Golden / 境界不足 | **進捗:** `fixtures/phase3/*`、symlink／`..`、`approve_dry_run` E2E。 |
| **運用** | Human Review UI なし | **CLI / 最小 API**（仕様 14.3；Phase 5 前倒し可） |
| **制度** | authority / PoP-UID | **Phase 4**（本計画では要件だけ列挙） |

## 3. 追加設計方針

### 3.1 evaluation_kind と evidence_basis

Phase 3 では、実行前評価と実行後評価を機械可読に区別する。

`evaluation_kind` は「いつ・どの種類の評価か」を示す。すでに `RDEResult.evaluation_kind` として `pre_synthetic` / `post_structural` が導入されている。

一方、`evidence_basis` は「その評価が何を根拠にしたか」を示す。これは、synthetic RDE と Structural/Semantic RDE の混同をさらに抑えるための追加課題である。

```python
EvaluationKind = Literal[
    "pre_synthetic",
    "post_structural",
    "post_semantic",
    "human_review",
]
```

```python
EvidenceBasis = Literal[
    "tool_risk_rule",
    "execution_contract",
    "structural_diff",
    "semantic_delta",
    "observed_side_effects",
    "rollback_result",
    "human_review_decision",
    "llm_assisted_semantic_evaluation",
]
```

初期推奨モデル：

```python
class EvaluationProvenance(BaseModel):
    evaluation_kind: EvaluationKind
    evidence_basis: list[EvidenceBasis]
    synthetic: bool = False
    evaluator_name: str | None = None
    evaluator_version: str | None = None
    explanation: str
```

これにより、`synthetic_rde_for_tool` が作る評価を、本来の StructuralDiff / SemanticDelta ベースの RDE と混同しない。

### 3.2 ExecutionGateEvaluation

外部 API がタプル戻り値へ依存しないよう、Phase 3 hardening では `ExecutionGateEvaluation` を導入する。

```python
class ExecutionGateEvaluation(BaseModel):
    evaluation_id: str
    tool_call: ToolCallRequest | None = None
    contract: ExecutionTaskContract
    decision: ExecutionGateDecision
    provenance: EvaluationProvenance | None = None
    created_at: datetime
```

現状では、`evaluate_before_execution()` が `ExecutionGateEvaluation` を返す。これは Wave A の大きな改善である。次の課題は、`provenance` または同等の監査根拠を埋め込むことである。

### 3.3 Phase3ExecutionEvaluationResult

PostExecutionDiff を既存 `run_phase1_evaluation` へ接続するだけでは、tool execution固有の文脈が欠落する可能性がある。

現状では `run_phase1_evaluation_from_post_execution_diff` により、少なくとも1パスで既存評価パイプラインへ接続できている。これはL1には十分である。ただし、L2以降では実行契約、observed side effects、rollback plan、review decisionを保持する集約型が必要になる可能性がある。

推奨候補：

```python
class Phase3ExecutionEvaluationResult(BaseModel):
    execution_evaluation_id: str
    tool_call: ToolCallRequest
    contract: ExecutionTaskContract
    gate_decision: ExecutionGateDecision
    execution_result: ToolExecutionResult
    post_execution_diff: PostExecutionDiff
    rde_result: RDEResult | None = None
    semantic_evaluation: SemanticEvaluationResult | None = None
    rollback_plan: RollbackPlan | None = None
    rollback_result: RollbackResult | None = None
    policy_decision: PolicyDecision | None = None
    audit_event_id: str | None = None
    provenance: EvaluationProvenance
    created_at: datetime
```

これにより、文書変換の `Phase1EvaluationResult` と、Agent実行後評価の `Phase3ExecutionEvaluationResult` を混同せずに接続できる。

### 3.4 external_side_effect_kind

`network_allowed` は粗い制御であり、本番境界では不足する。HTTP / external API を導入する前に、外部副作用の種類を分類する。

```python
ExternalSideEffectKind = Literal[
    "none",
    "read_only_fetch",
    "state_changing_request",
    "notification",
    "publishing",
    "payment_or_billing",
    "identity_or_auth",
    "data_exfiltration_risk",
    "legal_or_compliance_effect",
    "unknown",
]
```

初期Policy：

```text
read_only_fetch:
  allow only if domain allowlist and no credential leakage

state_changing_request:
  human_review required

notification / publishing:
  human_review required

payment_or_billing:
  halt unless explicit institutional approval

identity_or_auth:
  human_review or halt

data_exfiltration_risk:
  halt

legal_or_compliance_effect:
  human_review with authority check

unknown:
  human_review or halt
```

これにより、`network_allowed=true` だけで外部副作用を許可する誤りを避ける。

## 4. ウェーブ別ロードマップ

### Wave A — 説明責任と API の安定（L0→L1 の前提）

**目的：** 誤認リスクを下げ、マージ後の保守コストを抑える。

| ID | タスク | 完了条件（例） | 状態 |
|----|--------|----------------|------|
| A1 | synthetic フラグまたは別型で pre/post RDE を区別 | モデル・監査で `evaluation_kind` が機械可読 | **完了**（`RDEResult.evaluation_kind`、Phase 1 監査 payload、`schemas/rde_result.schema.json`） |
| A2 | `ExecutionGateEvaluation`（decision + contract） | 公開 API がタプルに依存しない | **完了**（破壊的変更あり） |
| A3 | CHANGELOG に `ModificationOutcome` 記載 | 破壊的変更が一文で分かる | **完了**（`CHANGELOG.md`） |
| A4 | `docs/audit_event_schema.md` を JSON スキーマと同期 | 同一 PR で整合 | **完了**（canonical を `schemas/audit_event.schema.json` に明記しコピー一致） |
| A5 | `evidence_basis` を導入 | RDE分類の根拠が `tool_risk_rule` / `structural_diff` / `semantic_delta` 等で機械可読 | **未** |

**期間目安：** 短サイクル（1–2 スプリント相当）。Wave A は A1–A4 までクローズ可能。A5 は追加hardening項目としてIssue化する。

### Wave B — 監査・実行後評価（L1 の核）

**目的：** 「止めた／実行した」を **JSONL 一次記録**で追えるようにする。

| ID | タスク | 完了条件（例） | 状態 |
|----|--------|----------------|------|
| B1 | `audit/log.py` に execution 系ヘルパ | gate / runtime / review イベントのビルダ＋ append | **完了**（`audit_event_execution_gate_evaluated` 等。blocked/completed は `audit_event_tool_execution` + action 引数で統一） |
| B2 | PostExecutionDiff → Phase 1 パイプライン | 統合テスト 1 本以上 | **完了**（`run_phase1_evaluation_from_post_execution_diff`、`tests/integration/test_post_execution_phase1_connector.py`） |
| B3 | SQLite `execution_events` と `audit_event_id` | append 時に ID 連携 | **完了**（`ToolExecutionResult.audit_event_id` を SQLite に保存） |
| B4 | Golden fixtures `fixtures/phase3/*` | CI で検証 | **完了**（`test_phase3_golden_fixtures.py`） |
| B5 | `Phase3ExecutionEvaluationResult` を検討 | tool実行文脈を落とさずRDE評価結果を保持する設計判断 | **未** |

Wave B のL1必須部分はクローズ可能。B5 はL2またはPhase 4接続前の設計課題として扱う。

### Wave C — 実行環境の実効性（L1→L2）

**目的：** 意図した制限（時間・ネットワーク・コマンド）が **実際に効く**。

| ID | タスク | 完了条件（例） | 状態 |
|----|--------|----------------|------|
| C1 | `max_runtime_ms` をプロセス kill で実装 | 長時間 sleep テストで `timed_out` | **未** |
| C2 | subprocess allowlist（コマンド・引数パターン） | ホワイトリスト外は `blocked` | **未** |
| C3 | `external_side_effect_kind` を導入 | HTTP実行前に外部副作用を分類可能 | **未** |
| C4 | HTTP クライアントを「プロキシ＋許可ドメイン」に限定 | contract の `network_allowed` と `external_side_effect_kind` が整合 | **未** |
| C5 | path 攻撃系テスト | symlink、 `..` 逸脱 | **一部完了**（`tests/unit/test_safe_execution_runtime.py`。Windows は symlink テスト skip。TOCTOU は未） |

### Wave D — スケールとデータモデル（L2）

**目的：** 複数エージェント・長期運用の最低条件。

| ID | タスク | 完了条件（例） | 状態 |
|----|--------|----------------|------|
| D1 | SQLite migration v2（review 全文列 or JSON） | 既存 DB の migrate 手順書 | **未** |
| D2 | 書き込みキュー or RelationStore マイクロサービス | 負荷方針の文書化 | **未** |
| D3 | Rollback：多ファイル・delete の E2E | 評価レポート P0/P1 を満たす | **未** |

### Wave E — Phase 4 接続（L3 への橋）

**目的：** Institution・説明責任の制度層へデータを渡せる。**状態: 未着手**（D 完了後キック推奨）。

```text
- reviewer_id と authority の対応
- irreversible operation の分類表と Policy への反映
- protected_resource と InstitutionRule の接続点（ID のみでも可）
```

詳細は **Phase 4 仕様書**側で主導する。本計画では **D 完了後** にキックを推奨。

## 5. Issue 化・Milestone 化方針

Wave A–E は、Issue 単位ではなく **Milestone または計画単位**として扱う。

Issue は A5、B5、C1 のような個別タスク単位で作成する。これにより、PR分割、レビュー、完了条件、CI確認が明確になる。

推奨ラベル：

```text
phase3-hardening
audit
runtime-safety
rde-semantics
relation-store
review-workflow
breaking-change
api-stability
post-execution-rde
network-boundary
```

推奨Milestone：

```text
Phase 3 L1 Internal Pilot Ready
Phase 3 L2 Bounded Production Ready
Phase 4 Institution Bridge
```

Issue化の粒度例：

```text
A5: Add evidence_basis to distinguish tool risk, structural diff, semantic delta
B5: Decide whether to introduce Phase3ExecutionEvaluationResult
C1: Implement process-kill based max_runtime_ms
C2: Add subprocess allowlist policy
C3: Add external_side_effect_kind taxonomy
D1: Add SQLite migration v2 plan for review payload persistence
```

## 6. 優先順位（評価レポート P との対応）

```text
P0（PR・CI）     → 継続的に維持（Wave A 文書・スキーマは実装済み）。
P1（MVP 完了線） → Wave A・B のL1必須部分は実装済み。Exit §7 の残りは「全経路監査組込み」程度の運用タスク。
P2（Phase 4 前） → A5 + B5 + Wave C の C1–C3 + Wave D の D1（C5 の残は TOCTOU 等）
P3（将来）       → Wave C4–C5、D2、git_patch_reverse、container 等
```

## 7. 完了の定義（Exit criteria）

次を満たしたら **「Phase 3 を L1 internal-pilot ready と呼べる」** と内部で合意できる。**2026-05 実装反映**に応じたチェックを併記する。

| # | 基準 | 2026-05 時点 |
|---|------|----------------|
| 1 | 実行前ゲート・実行結果・レビュー決定が AuditLog（JSONL）上で追跡できる | **ほぼ達成** — ヘルパと統合テスト（`test_agent_execution_gate_flow`）でゲート／レビュー／実行後の追跡を実証。アプリ全 API での強制 append は未。 |
| 2 | PostExecutionDiff から少なくとも 1 パスで RDE 再評価に接続できる | **達成** — `run_phase1_evaluation_from_post_execution_diff` + 統合テスト。 |
| 3 | synthetic / structural の区別が監査またはモデルで機械可読 | **達成** — `evaluation_kind`、`audit_event_execution_gate_evaluated` の payload。 |
| 4 | RDE分類の根拠が `evidence_basis` として機械可読 | **未** — 追加hardening対象。 |
| 5 | パス traversal / symlink に対する回帰テストがある | **達成**（最小限）— `..` と POSIX symlink。TOCTOU は未。 |
| 6 | approve_dry_run から runtime 再開までの E2E が 1 本以上ある | **達成** — `test_human_review_approve_dry_run_then_runtime`。 |
| 7 | GitHub Actions が main / release ブランチで緑を維持している | **運用確認** — マージ後に CI を確認すること。 |

L2 を宣言するには、さらに **C1–C4**（実効 timeout、allowlist、外部副作用分類、制限付きネット）と **D1**（migration）を満たすことを推奨する。

## 8. 明示的にスコープ外（仕様どおり）

次は **本計画の「解消」対象に含めない**（別プログラム）。

```text
- 完全 OS sandbox の保証
- 暗号学的に改ざん耐性のある AuditLog
- PoP-UID / 完全な Institution Layer
- 任意クラウド API との全面互換
- LLM evaluator アンサンブルの本番運用
```

必要になった時点で **L3 / Phase 5** のイニシアチブとして起案する。

## 9. RDE差異検証

### 9.1 保存された要素

本計画は、Phase 3 MVPの中核であるAgent Execution Gate、SQLiteRelationStore、Safe Execution Runtime、Rollback Manager、Human Review Workflow、Optional Semantic Evaluatorを保存している。また、RDE / Policy / Runtime / Review / Rollback の責務分離も維持している。

### 9.2 変換された要素

`docs/32` のP0–P3課題を、Wave A–E、成熟度L0–L3、Exit criteria、Issue化方針へ変換した。

この変換は、品質採点ではなく、意味変化ΔMの制度的管理計画への変換である。すなわち、Phase 3を「実装済み」として閉じるのではなく、「どの条件下で内部利用可能か」「どの条件で限定本番可能か」を明示した。

### 9.3 補完された要素

以下を補完した。

```text
- L1を production-ready ではなく internal-pilot ready とする区別
- L2を bounded production ready とする区別
- evaluation_kind / evidence_basis
- EvaluationProvenance
- ExecutionGateEvaluation
- Phase3ExecutionEvaluationResult
- external_side_effect_kind
- Issue / Milestone / Label 方針
```

### 9.4 未解決のまま残した要素

以下は未解決として残す。

```text
- 完全OS sandbox
- cryptographic audit
- Institution / authority / PoP-UID
- LLM evaluator ensemble production operation
- external cloud API全面互換
```

これらは本計画のL3またはPhase 4/5の対象である。

### 9.5 逸脱リスク

主な逸脱リスクは以下である。

```text
- L1を本番投入可能と誤認する
- synthetic RDEをStructural/Semantic RDEと誤認する
- network_allowedだけで外部副作用を許可する
- Phase1EvaluationResultへ実行後評価を単純流用し、実行文脈を落とす
- Waveを大きすぎるIssueとして作成し、完了条件が曖昧になる
```

本改訂では、これらのリスクを抑えるため、L1/L2の呼称、evaluation provenance、Phase3ExecutionEvaluationResult、external_side_effect_kind、Issue粒度方針を追加した。

## 10. 次のアクション

1. **A5・B5・Wave C1–C4・D** を **GitHub Issues** に分解（WaveはMilestoneまたは計画単位）。Wave A1–A4・B1–B4 はクローズ可。  
2. `docs/32` §8.6 — 本書（§0.1・§7）への参照でバックログを置き換え済みなら、Issue 番号の追記のみ。  
3. **L1 宣言**前に: 監査 append を主要エントリポイントへ組込むか方針決定、CI 緑の確認。  
4. スプリントごとに **§7 Exit criteria** 表を更新する。  
5. 最初の hardening PR 候補は A5（`evidence_basis`）と C3（`external_side_effect_kind`）。

## 11. 改訂履歴

| 版 | 日付 | 内容 |
|----|------|------|
| 0.1 | 2026-05-04 | 初版（L0–L3 定義、Wave A–E、Exit criteria） |
| 0.2 | 2026-05-04 | Wave A/B 中核を実装（`ExecutionGateEvaluation`、`evaluation_kind`、監査ヘルパ、PostExecution→Phase1、Golden、パス／approve_dry_run E2E）。Wave C–E は未着手。 |
| 0.3 | 2026-05-04 | 実装済み内容を本文に反映（§0.1 サマリ、§2 進捗列、Wave A–C 状態列、§5 Exit チェック表、§7 更新）。 |
| 0.4 | 2026-05-04 | 評価指摘を反映。L1をinternal-pilot readyへ修正、`evidence_basis`、`EvaluationProvenance`、`Phase3ExecutionEvaluationResult`、`external_side_effect_kind`、Issue粒度方針を追加。 |
