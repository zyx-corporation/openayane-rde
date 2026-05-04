# SQLiteRelationStore: migration v2 計画（レビュー payload 永続化）

## 1. 目的

Phase 3 の `SQLiteRelationStore` は MVP として `review_requests` 等に JSON 列を併用している。長期運用と authority / Institution 連携を見据え、**レビュー文脈を欠落なく保存**しつつ、**AuditLog（JSONL）を一次記録**とする方針を維持する。

関連 Issue: **D1**（SQLite migration v2）。

## 2. 現状（schema version 1）

- `schema_migrations` テーブルで適用バージョンを記録する。
- `review_requests` は `risk_json`、`rollback_plan_json`、`rde_result_json`、`relation_context_json` 等で部分保存している。
- 完全な `ReviewRequest` / ゲート文脈は、JSONL 監査とアプリ層の組合せに依存しうる。

## 3. v2 で検討する変更

### 3.1 レビュー payload

**推奨（v2 初期）**

- `review_requests.payload_json`（TEXT）を追加し、`ReviewRequest.model_dump(mode="json")` の完全スナップショットを保存する。
- 既存の正規化列（`contract_id`、`tool_call_id`、`status` 等）は **クエリ用に維持**し、JSON は **再現性・監査補助**とする。

**代替**

- 列のみ正規化拡張（Reviewer・期限・policy 参照など）— スキーマ変更コストが高いため、v2 では JSON 完全列を優先し、必要な列だけ段階的に追加する。

### 3.2 必須フィールド（監査・制度接続用）

次を payload または列で必ず辿れること（v2 受入基準）:

```text
- review_request_id, contract_id, tool_call_id, agent_id, status
- reason, risk（ToolCallRisk）
- created_at, updated_at
- 可能なら last_audit_event_id（ゲート／レビュー要求の監査行との外部キーは文字列 ID のみ）
```

### 3.3 移行手順（v1 → v2）

1. バックアップ（ファイルコピー）。
2. アプリ起動時または明示 `migrate` コマンドで `PRAGMA user_version` または `schema_migrations` を確認。
3. トランザクション内で `ALTER TABLE review_requests ADD COLUMN payload_json TEXT`（および将来の列）。
4. 既存行: `payload_json` が NULL の間は、既存 JSON 列から **ベストエフォートで再構成**するマイグレーションスクリプトを 1 回実行（失敗時は NULL のまま、ログに記録）。
5. `INSERT INTO schema_migrations (version, name, applied_at) VALUES (2, 'review_payload_v2', ...)`。

### 3.4 テスト方針

- 新規 DB: v2 初期化で `applied_schema_versions()` が `[1, 2]` を含むこと。
- v1 フィクスチャ DB ファイル: マイグレーション後に `ReviewRequest` を読み戻せること（フィクスチャはリポジトリに最小 1 個）。
- **AuditLog が真実** — SQLite は索引・運用キャッシュとして扱い、法的・制度的に必須な説明は JSONL を正とする。

## 4. 実装順序（推奨）

1. 本書のレビューにより v2 列一覧を確定する。
2. `SQLiteRelationStore` に `SCHEMA_VERSION = 2` 用の `_migrate_v1_to_v2` を実装する。
3. 上記テストを追加する。
4. `docs/33` Wave D1 の状態を「実装済み」に更新する。

## 5. 改訂履歴

| 版 | 日付 | 内容 |
|----|------|------|
| 0.1 | 2026-05-04 | 初版（Issue D1 受入向け計画） |
