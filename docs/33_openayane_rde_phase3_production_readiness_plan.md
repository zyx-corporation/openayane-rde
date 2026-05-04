---
title: "OpenAyane RDE Phase 3 production-ready 制約解消計画"
version: "0.1"
date: "2026-05-04"
status: "planning"
---

# OpenAyane RDE Phase 3：production-ready 制約解消計画

## 0. 文書情報

文書名：Phase 3「production-ready ではない」制約の解消計画  
対象：`docs/30` Phase 3 仕様、`docs/31` 実装レポート、`docs/32` 評価レポートで明示された限界  
位置づけ：**ロードマップ**（Issue 化・スプリント分割の入力）

関連：

```text
- docs/30_openayane_rde_phase3_specification.md（非目的・逸脱リスク）
- docs/31_openayane_rde_phase3_implementation_report.md（技術的負債一覧）
- docs/32_openayane_rde_phase3_evaluation_report.md（P0–P3 課題）
```

## 1. 「production-ready」の定義（段階）

本リポジトリでは **単一の boolean** ではなく、**運用シナリオ別の到達レベル**で定義する。

| レベル | 呼称 | 目安 |
|--------|------|------|
| L0 | **Lab / MVP** | 現状。単一プロセス・限定ファイル操作・シェル未実行。 |
| L1 | **内部パイロット** | 監査一貫性・実行後 RDE 接続・レビュー E2E・パス安全性テストが揃う。 |
| L2 | **信頼境界付き本番** | allowlist 付き subprocess / 制限付きネットワーク・タイムアウト実効・SQLite 書き込みキューまたは単一 writer サービス化。 |
| L3 | **高保証** | コンテナ等の隔離、Institution / authority 連携、暗号学的監査は **Phase 4 以降**（仕様非目的の範囲を含む）。 |

**制約解消計画**は主に **L0 → L1** と **L1 → L2** を対象とする。L3 は本計画では **スコープ外** とし、Phase 4 計画へ接続する。

## 2. 現状制約の整理（評価レポート対応表）

| 領域 | 制約・リスク | 解消の方向性 |
|------|----------------|--------------|
| **概念** | synthetic RDE と本番 RDE の混同 | 型・metadata・監査ペイロードで **Pre-execution 合成** を明示；命名整理（例: `ToolRiskRDEResult`） |
| **API** | ゲートがタプル返却 | `ExecutionGateEvaluation` 等の **集約モデル** で外部 API 安定化 |
| **互換** | `ModificationOutcome` リネーム | **移行ガイド**（CHANGELOG / README） |
| **Runtime** | シェル・HTTP 未実行、timeout 近似 | **allowlist subprocess**、**プロキシ経由 HTTP**、**実効 timeout（kill）** を段階導入 |
| **Runtime** | symlink / TOCTOU | **パス正規化・テスト**、必要なら open 時 fd 検証 |
| **Rollback** | file_snapshot 中心 | 多ファイル・delete E2E；**git_patch_reverse** は P2 以降 |
| **永続化** | SQLite 単一 writer | **書き込みキュー**または **RelationStore サービス**（単一プロセス RPC） |
| **永続化** | review 列不足 | **migration v2** で payload 完全保存 |
| **監査** | AuditLog 統合が薄い | **execution 系 append ヘルパ**、event_id の相互参照 |
| **RDE** | PostExecutionRDE 未配線 | `PostExecutionDiff` → **既存評価パイプライン**への最小コネクタ |
| **テスト** | Golden / 境界不足 | `fixtures/phase3`、symlink、approve_dry_run E2E |
| **運用** | Human Review UI なし | **CLI / 最小 API**（仕様 14.3；Phase 5 前倒し可） |
| **制度** | authority / PoP-UID | **Phase 4**（本計画では要件だけ列挙） |

## 3. ウェーブ別ロードマップ

### Wave A — 説明責任と API の安定（L0→L1 の前提）

**目的：** 誤認リスクを下げ、マージ後の保守コストを抑える。

| ID | タスク | 完了条件（例） |
|----|--------|----------------|
| A1 | synthetic フラグまたは別型で pre/post RDE を区別 | 監査 payload に `evaluation_kind: pre_synthetic \| post_structural` |
| A2 | `ExecutionGateEvaluation`（decision + contract + メタ） | 公開 API がタプルに依存しない |
| A3 | CHANGELOG に `ModificationOutcome` 記載 | 破壊的変更が一文で分かる |
| A4 | `docs/audit_event_schema.md` を JSON スキーマと同期 | 差分ゼロ |

**期間目安：** 短サイクル（1–2 スプリント相当）。

### Wave B — 監査・実行後評価（L1 の核）

**目的：** 「止めた／実行した」を **JSONL 一次記録**で追えるようにする。

| ID | タスク | 完了条件（例） |
|----|--------|----------------|
| B1 | `audit/log.py` に execution 系ヘルパ | gate / blocked / completed / review が同一形式で append |
| B2 | PostExecutionDiff → `run_phase1_evaluation` または薄いラッパ | 統合テスト 1 本以上 |
| B3 | SQLite `execution_events` と `audit_event_id` の対応 | upsert または append 時に ID 連携 |
| B4 | Golden fixtures `fixtures/phase3/*` | CI で読み取り検証 |

### Wave C — 実行環境の実効性（L1→L2）

**目的：** 意図した制限（時間・ネットワーク・コマンド）が **実際に効く**。

| ID | タスク | 完了条件（例） |
|----|--------|----------------|
| C1 | `max_runtime_ms` をプロセス kill で実装 | 長時間 sleep テストで `timed_out` |
| C2 | subprocess allowlist（コマンド・引数パターン） | ホワイトリスト外は `blocked` |
| C3 | HTTP クライアントを「プロキシ＋許可ドメイン」に限定 | contract の `network_allowed` と整合 |
| C4 | path 攻撃系テスト | symlink、 `..` 逸脱のケース |

### Wave D — スケールとデータモデル（L2）

**目的：** 複数エージェント・長期運用の最低条件。

| ID | タスク | 完了条件（例） |
|----|--------|----------------|
| D1 | SQLite migration v2（review 全文列 or JSON） | 既存 DB の migrate 手順書 |
| D2 | 書き込みキュー or RelationStore マイクロサービス | 同時書き込み負荷テスト方針が文書化されている |
| D3 | Rollback：多ファイル・delete の E2E | 評価レポート P0/P1 を満たす |

### Wave E — Phase 4 接続（L3 への橋）

**目的：** Institution・説明責任の制度層へデータを渡せる。

```text
- reviewer_id と authority の対応
- irreversible operation の分類表と Policy への反映
- protected_resource と InstitutionRule の接続点（ID のみでも可）
```

詳細は **Phase 4 仕様書**側で主導する。本計画では **D 完了後** にキックを推奨。

## 4. 優先順位（評価レポート P との対応）

```text
P0（PR・CI）     → Wave A の一部（文書・スキーマ）と独立。継続的に維持。
P1（MVP 完了線） → Wave A 全体 + Wave B の B1–B2 + B4 の一部
P2（Phase 4 前） → Wave B 完了 + Wave C の C1–C2 + Wave D の D1
P3（将来）       → Wave C3–C4、D2、git_patch_reverse、container 等
```

## 5. 完了の定義（Exit criteria）

次を満たしたら **「Phase 3 を L1 production-ready と呼んよい」** と内部で合意できる（例）。

```text
1. 実行前ゲート・実行結果・レビュー決定が AuditLog（JSONL）上で追跡できる
2. PostExecutionDiff から少なくとも 1 パスで RDE 再評価に接続できる
3. synthetic / structural の区別が監査またはモデルで機械可読
4. パス traversal / symlink に対する回帰テストがある
5. approve_dry_run から runtime 再開までの E2E が 1 本以上ある
6. GitHub Actions が main / release ブランチで緑を維持している
```

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

1. 本計画の Wave A–D を **GitHub Issues** に分解（ラベル `phase3-hardening` 等）。  
2. `docs/32` §8.6 の backlog 作成と本書を相互リンクする。  
3. スプリントごとに **Exit criteria** のチェックリストを更新する。

## 8. 改訂履歴

| 版 | 日付 | 内容 |
|----|------|------|
| 0.1 | 2026-05-04 | 初版（L0–L3 定義、Wave A–E、Exit criteria） |
