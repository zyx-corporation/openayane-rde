---
title: "OpenAyane RDE Phase 3 production-ready 制約解消計画"
version: "0.3"
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

本リポジトリでは **単一の boolean** ではなく、**運用シナリオ別の到達レベル**で定義する。

| レベル | 呼称 | 目安 |
|--------|------|------|
| L0 | **Lab / MVP** | 単一プロセス・限定ファイル操作・シェル未実行（タイムアウトは近似）。 |
| L1 | **内部パイロット** | 監査ヘルパ・PostExecution→Phase1・`evaluation_kind`・パス回帰・approve_dry_run E2E まで **実装済み**。全エントリポイントへの監査組込みと CI 緑の継続は運用で確認。 |
| L2 | **信頼境界付き本番** | allowlist 付き subprocess / 制限付きネットワーク・タイムアウト実効・SQLite 書き込みキューまたは単一 writer サービス化。 |
| L3 | **高保証** | コンテナ等の隔離、Institution / authority 連携、暗号学的監査は **Phase 4 以降**（仕様非目的の範囲を含む）。 |

**制約解消計画**は主に **L0 → L1** と **L1 → L2** を対象とする。L3 は本計画では **スコープ外** とし、Phase 4 計画へ接続する。

## 2. 現状制約の整理（評価レポート対応表）

| 領域 | 制約・リスク | 解消の方向性 |
|------|----------------|--------------|
| **概念** | synthetic RDE と本番 RDE の混同 | **進捗:** `RDEResult.evaluation_kind` と監査 payload。命名整理（別型化）は任意。 |
| **API** | ゲートがタプル返却 | **完了:** `ExecutionGateEvaluation`（`evaluate_before_execution` の戻り値）。 |
| **互換** | `ModificationOutcome` リネーム | **進捗:** `CHANGELOG.md` 記載。README への短い言及は任意。 |
| **Runtime** | シェル・HTTP 未実行、timeout 近似 | **allowlist subprocess**、**プロキシ経由 HTTP**、**実効 timeout（kill）** を段階導入 |
| **Runtime** | symlink / TOCTOU | **進捗:** `..` 逸脱・ワークスペース外 symlink の回帰テスト。TOCTOU / fd 検証は未。 |
| **Rollback** | file_snapshot 中心 | 多ファイル・delete E2E；**git_patch_reverse** は P2 以降 |
| **永続化** | SQLite 単一 writer | **書き込みキュー**または **RelationStore サービス**（単一プロセス RPC） |
| **永続化** | review 列不足 | **migration v2** で payload 完全保存 |
| **監査** | AuditLog 統合が薄い | **進捗:** execution 系イベントビルダと `append_audit_event`；ゲート／実行結果と `audit_event_id` の対応は **SQLite + モデル**で可。全経路での自動 append は未。 |
| **RDE** | PostExecutionRDE 未配線 | **完了:** `run_phase1_evaluation_from_post_execution_diff`。 |
| **テスト** | Golden / 境界不足 | **進捗:** `fixtures/phase3/*`、symlink／`..`、`approve_dry_run` E2E。 |
| **運用** | Human Review UI なし | **CLI / 最小 API**（仕様 14.3；Phase 5 前倒し可） |
| **制度** | authority / PoP-UID | **Phase 4**（本計画では要件だけ列挙） |

## 3. ウェーブ別ロードマップ

### Wave A — 説明責任と API の安定（L0→L1 の前提）

**目的：** 誤認リスクを下げ、マージ後の保守コストを抑える。

| ID | タスク | 完了条件（例） | 状態 |
|----|--------|----------------|------|
| A1 | synthetic フラグまたは別型で pre/post RDE を区別 | モデル・監査で `evaluation_kind` が機械可読 | **完了**（`RDEResult.evaluation_kind`、Phase 1 監査 payload、`schemas/rde_result.schema.json`） |
| A2 | `ExecutionGateEvaluation`（decision + contract） | 公開 API がタプルに依存しない | **完了**（破壊的変更あり） |
| A3 | CHANGELOG に `ModificationOutcome` 記載 | 破壊的変更が一文で分かる | **完了**（`CHANGELOG.md`） |
| A4 | `docs/audit_event_schema.md` を JSON スキーマと同期 | 同一 PR で整合 | **完了**（canonical を `schemas/audit_event.schema.json` に明記しコピー一致） |

**期間目安：** 短サイクル（1–2 スプリント相当）。**Wave A はクローズ可能。**

### Wave B — 監査・実行後評価（L1 の核）

**目的：** 「止めた／実行した」を **JSONL 一次記録**で追えるようにする。

| ID | タスク | 完了条件（例） | 状態 |
|----|--------|----------------|------|
| B1 | `audit/log.py` に execution 系ヘルパ | gate / runtime / review イベントのビルダ＋ append | **完了**（`audit_event_execution_gate_evaluated` 等。blocked/completed は `audit_event_tool_execution` + action 引数で統一） |
| B2 | PostExecutionDiff → Phase 1 パイプライン | 統合テスト 1 本以上 | **完了**（`run_phase1_evaluation_from_post_execution_diff`、`tests/integration/test_post_execution_phase1_connector.py`） |
| B3 | SQLite `execution_events` と `audit_event_id` | append 時に ID 連携 | **完了**（`ToolExecutionResult.audit_event_id` を SQLite に保存） |
| B4 | Golden fixtures `fixtures/phase3/*` | CI で検証 | **完了**（`test_phase3_golden_fixtures.py`） |

**Wave B はクローズ可能。** 今後の伸ばしどころ: 全実行パスでのヘルパ呼び出しの標準化、B1 の「blocked」専用ラッパの有無は運用で選択。

### Wave C — 実行環境の実効性（L1→L2）

**目的：** 意図した制限（時間・ネットワーク・コマンド）が **実際に効く**。

| ID | タスク | 完了条件（例） | 状態 |
|----|--------|----------------|------|
| C1 | `max_runtime_ms` をプロセス kill で実装 | 長時間 sleep テストで `timed_out` | **未** |
| C2 | subprocess allowlist（コマンド・引数パターン） | ホワイトリスト外は `blocked` | **未** |
| C3 | HTTP クライアントを「プロキシ＋許可ドメイン」に限定 | contract の `network_allowed` と整合 | **未** |
| C4 | path 攻撃系テスト | symlink、 `..` 逸脱 | **一部完了**（`tests/unit/test_safe_execution_runtime.py`。Windows は symlink テスト skip。TOCTOU は未） |

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

## 4. 優先順位（評価レポート P との対応）

```text
P0（PR・CI）     → 継続的に維持（Wave A 文書・スキーマは実装済み）。
P1（MVP 完了線） → Wave A・B は実装済み。Exit §5 の残りは「全経路監査組込み」程度の運用タスク。
P2（Phase 4 前） → Wave C の C1–C2 + Wave D の D1（C4 の残は TOCTOU 等）
P3（将来）       → Wave C3、D2、git_patch_reverse、container 等
```

## 5. 完了の定義（Exit criteria）

次を満たしたら **「Phase 3 を L1 production-ready と呼んよい」** と内部で合意できる（例）。**2026-05 実装反映**に応じたチェックを併記する。

| # | 基準 | 2026-05 時点 |
|---|------|----------------|
| 1 | 実行前ゲート・実行結果・レビュー決定が AuditLog（JSONL）上で追跡できる | **ほぼ達成** — ヘルパと統合テスト（`test_agent_execution_gate_flow`）でゲート／レビュー／実行後の追跡を実証。アプリ全 API での強制 append は未。 |
| 2 | PostExecutionDiff から少なくとも 1 パスで RDE 再評価に接続できる | **達成** — `run_phase1_evaluation_from_post_execution_diff` + 統合テスト。 |
| 3 | synthetic / structural の区別が監査またはモデルで機械可読 | **達成** — `evaluation_kind`、`audit_event_execution_gate_evaluated` の payload。 |
| 4 | パス traversal / symlink に対する回帰テストがある | **達成**（最小限）— `..` と POSIX symlink。TOCTOU は未。 |
| 5 | approve_dry_run から runtime 再開までの E2E が 1 本以上ある | **達成** — `test_human_review_approve_dry_run_then_runtime`。 |
| 6 | GitHub Actions が main / release ブランチで緑を維持している | **運用確認** — マージ後に CI を確認すること。 |

L2 を宣言するには、さらに **C1–C3**（実効 timeout、allowlist、制限付きネット）と **D1**（migration）を満たすことを推奨する。

## 6. 明示的にスコープ外（仕様どおり）

次は **本計画の「解消」対象に含めない**（別プログラム）。

```text
- 完全 OS sandbox の保証
- 暗号学的に改ざん耐性のある AuditLog
- PoP-UID / 完全な Institution Layer
- 任意クラウド API との全面互換
- LLM evaluator アンサンブルの本番運用
```

必要になった時点で **L3 / Phase 5** のイニシアチブとして起案する。

## 7. 次のアクション

1. **Wave C1–C3・D** を **GitHub Issues** に分解（ラベル `phase3-hardening` 等）。Wave A・B はクローズ可。  
2. `docs/32` §8.6 — 本書（§0.1・§5）への参照でバックログを置き換え済みなら、Issue 番号の追記のみ。  
3. **L1 宣言**前に: 監査 append を主要エントリポイントへ組込むか方針決定、CI 緑の確認。  
4. スプリントごとに **§5 Exit criteria** 表を更新する。

## 8. 改訂履歴

| 版 | 日付 | 内容 |
|----|------|------|
| 0.1 | 2026-05-04 | 初版（L0–L3 定義、Wave A–E、Exit criteria） |
| 0.2 | 2026-05-04 | Wave A/B 中核を実装（`ExecutionGateEvaluation`、`evaluation_kind`、監査ヘルパ、PostExecution→Phase1、Golden、パス／approve_dry_run E2E）。Wave C–E は未着手。 |
| 0.3 | 2026-05-04 | 実装済み内容を本文に反映（§0.1 サマリ、§2 進捗列、Wave A–C 状態列、§5 Exit チェック表、§7 更新）。 |
