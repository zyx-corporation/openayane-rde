---
title: "OpenAyane RDE Phase 3 実装レポート"
version: "0.1"
date: "2026-05-04"
status: "phase 3 implementation summary"
---

# OpenAyane RDE Phase 3 実装レポート

## 0. 文書情報

文書名：OpenAyane RDE Phase 3 実装レポート  
対象リポジトリ：`zyx-corporation/openayane-rde`  
前提仕様：`docs/30_openayane_rde_phase3_specification.md`  
作成日：2026-05-04  
位置づけ：Phase 3 実装の達成範囲・逸脱・残課題の記録  

参照ブランチ／コミットは運用に応じて Git で確認すること（本文では固定しない）。

## 1. 総括

Phase 3 詳細仕様に対し、**Agent Execution Gate・SQLiteRelationStore・Safe Execution Runtime・Rollback Manager・Human Review Workflow・rule-based Semantic Evaluator** をコードとして結合した**最小一巡**の実装が行われた。CI（pytest / ruff / mypy）を通す前提で、型・スキーマ・ユニット／統合テストで主要パスを固定している。

一方、仕様の**非目的**（完全 OS sandbox、外部 Agent 全面互換等）に明記された範囲は意図的に未実装とし、**課題（次工程）**として本レポートに集約する。

```text
Phase 3 実装レポート上の位置づけ: 条件付き達成
  - 中核ループ（契約化 → リスク → 方針 → ゲート → 実行／レビュー）: 最小実装として成立
  - 本番同等の安全性・完全な意味再評価: 未達（仕様上も Phase 3 非目的に含まれる）
```

## 2. 仕様との対応（実装済み）

### 2.1 データモデル

`src/openayane_rde/core/models.py` に、仕様 8 章に相当する型を追加・整備した。

```text
- ToolCallRequest, ExecutionTaskContract, ToolCallRisk
- ExecutionGateDecision
- ToolExecutionResult（仕様上の Post-execution ExecutionResult に相当。旧 Phase1 の ExecutionResult は ModificationOutcome へリネーム）
- PostExecutionDiff, RollbackPlan, RollbackResult
- ReviewRequest, ReviewDecision
- SemanticEvaluationRequest, SemanticEvaluationResult
- AuditActionKind 拡張（実行・レビュー・rollback・semantic 監査用）
```

### 2.2 SQLiteRelationStore

`src/openayane_rde/relation/sqlite_store.py`：仕様 9 章のテーブル群・インデックス、`initialize`、relation の get/upsert、drift 行、execution/review/rollback 補助 API。

### 2.3 RelationStore 互換

`RelationStore` プロトコルに `relation_type`（デフォルト `generator-document`）を追加。`JSONRelationStore` は**旧 2 セグメントキー**の読み取り互換を残す。

### 2.4 ツール契約・リスク・ゲート

- `src/openayane_rde/agent/tool_contract.py`：正規化、契約生成、**ルールベース** `ToolCallRisk`
- `src/openayane_rde/policy/execution_rules.py`：`ExecutionPolicyConfig`、合成 RDE、方針決定
- `src/openayane_rde/agent/execution_gate.py`：`evaluate_before_execution`（**戻り値は (ExecutionGateDecision, ExecutionTaskContract) タプル**）、`enforce_execution_decision`

### 2.5 実行と rollback

- `src/openayane_rde/runtime/safe_execution.py`：ワークスペース制限付き read/write/delete、dry-run、network 拒否、保護リソース二重チェック
- `src/openayane_rde/runtime/rollback.py`：`RollbackManager`（`file_snapshot` 中心）
- `src/openayane_rde/runtime/post_execution.py`：最小 `PostExecutionDiff` 生成

### 2.6 Human Review

`src/openayane_rde/review/workflow.py`：メモリキュー＋任意で `SQLiteRelationStore` 永続化。`review/models.py` は core からの再エクスポート。

### 2.7 Optional Semantic Evaluator

`src/openayane_rde/semantic/evaluator.py`：`RuleBasedSemanticEvaluator`、LLM 用 stub。

### 2.8 JSON Schema 同期

`schemas/audit_event.schema.json` の `action` enum を `AuditActionKind` と一致させる（`test_schema_model_sync` 前提）。

### 2.9 テスト

```text
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

## 3. 意図的な逸脱・簡略化

仕様 4 章（非目的）および 20 章（逸脱リスク）に照らし、次を**意図的に最小化**した。

```text
- 完全な OS サンドボックス: 未実装（アプリ層制御のみ）
- 任意 external service 互換: 未実装
- shell / network の実実行: 最小実装ではブロックまたはシミュレーション
- LLM evaluator の本格運用: stub のみ
- Institution / PoP-UID / 暗号学的監査: 対象外
```

## 4. 課題（残務・技術的負債）

以下は**未完了または強化が必要**な項目である。優先度は運用リスクに応じて調整すること。

### 4.1 API・設計

| 課題 | 内容 |
|------|------|
| **ゲート API の戻り値** | `evaluate_before_execution` が `(ExecutionGateDecision, ExecutionTaskContract)` を返すのは実装上の都合。仕様の単一戻り値と異なるため、**NamedTuple 化・ゲート型への契約埋め込み**などで外部 API を安定化する余地がある。 |
| **合成 RDE の意味** | `synthetic_rde_for_tool` は **ToolCallRisk からの便宜的な分類**であり、StructuralDiff ベースの本評価ではない。監査説明とドキュメントで誤認を防ぐ必要がある。 |
| **ModificationOutcome リネーム** | Phase 1 の `ExecutionResult` を `ModificationOutcome` に変更。**外部利用者がいれば移行ガイドが必要**。 |

### 4.2 実行・安全性

| 課題 | 内容 |
|------|------|
| **シェル／ネットワーク** | 実シェル実行・実 HTTP は行わない。今後、ホワイトリスト subprocess・プロキシ経由 API など段階的導入が必要。 |
| **タイムアウト** | `max_runtime_ms` を sleep で近似している箇所があり、**長時間ブロッキング IO** には未対応。スレッド／async／プロセス kill が必要。 |
| **リソース上限** | メモリ・同時実行数などは未モデル化。 |

### 4.3 Rollback

| 課題 | 内容 |
|------|------|
| **git_patch_reverse / transactional** | Phase 3 最小実装では **`file_snapshot` 中心**。reverse patch・トランザクション戦略は未実装またはスタブに近い。 |
| **snapshot と target の対応** | 複数ファイル・ワイルドカードパスの edge case で復旧が不完全になりうる。**結合テストの拡充**が必要。 |

### 4.4 永続化・運用

| 課題 | 内容 |
|------|------|
| **SQLite 単一 writer** | 仕様どおり単一プロセス前提。**複数 Agent 同時書き込み**にはキューまたはサービス化が必要。 |
| **metadata_json の肥大化** | プロファイル等を JSON に寄せているため、**スキーマ migration と列正規化**の検討余地がある。 |
| **ReviewRequest の列不足** | DB に `proposed_action_summary` 等が無く、**全文はメモリ側／将来マイグレーション**で補完する余地あり。 |

### 4.5 監査・RDE 連携

| 課題 | 内容 |
|------|------|
| **AuditLog への実イベント append** | `AuditActionKind` は拡張済みだが、**ゲート／実行／レビューを JSONL に統一的に書くヘルパ**は薄い。運用では `audit/log.py` 周辺の拡張が望ましい。 |
| **PostExecutionRDE** | `PostExecutionDiff` 生成まではあるが、**既存 `run_phase1_evaluation` への自動接続**は未配線。実行後ループの一本化は次フェーズ。 |

### 4.6 テスト・フィクスチャ

| 課題 | 内容 |
|------|------|
| **Golden / fixtures** | 仕様 18.3 の `fixtures/phase3/...` は**未整備**。回帰のため追加推奨。 |
| **human_review 実行フロー統合** | `approve_dry_run` から runtime 再開までの E2E は**テストが薄い**。 |

### 4.7 ドキュメント

| 課題 | 内容 |
|------|------|
| **audit_event_schema（ドキュメント）** | `schemas/audit_event.schema.json` は更新済みだが、`docs/audit_event_schema.md` 等の**文言追随**が未完了の可能性がある。 |
| **README Phase 3** | 利用者向けに Phase 3 の**前提・限界**を README に短く追記するとよい。 |

## 5. Phase 4 接続条件（仕様 21 章）とのギャップ

仕様 21 章に列挙された Phase 4 前提のうち、次は**まだ弱いまたは部分的**である。

```text
- 実行判断の監査ストリーム一貫性: ヘルパ・運用ルールの整備が必要
- rollback 不可操作の網羅的識別: ルール拡張とテストが必要
- ReviewRequest における判断材料の完全性: DB 列・payload 設計の見直し余地
```

## 6. 結論

Phase 3 は、**「評価・履歴・Policy を Agent 実行制御に接続する」**という目的に対し、コード構造とテストで**最小実装ループを成立**させた。

ただし、**実運用レベルの安全性・完全な実行意味評価・Institution 層**は本フェーズの範囲外または課題として残る。次のイテレーションでは、本レポート第 4 章の課題を**優先度付きバックログ**に落とし、`docs/30` の非目的と照合しながら Phase 3 の「完了」ラインを組織内で合意することが望ましい。
