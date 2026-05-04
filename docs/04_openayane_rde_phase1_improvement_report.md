---
title: "OpenAyane RDE Phase 1 実装改善レポート"
date: "2026-05-04"
status: "working notes"
source: "チャットにて整理された評価・改善提案（セッション入力に基づく）"
---

# OpenAyane RDE Phase 1 実装改善レポート

本文は、現時点の実装に対する総合評価・優先改善項目・設計上の注意を整理したものです。リポジトリへの反映として、`Phase1EvaluationResult` の導入、CI、スキーマ／モデル同期テスト、監査ハッシュ検証の強化がこのドキュメント作成時点で進められています（詳細は Git 履歴を参照）。

## 0. 総合評価

Phase 1 Structural RDE MVP としては概ね成功している。RDE を実行主体とせず `RDEResult` を返す評価器とし、`PolicyBridge` が実行判断へ変換する構造は、「RDE は評価器、OpenAyane は機構」という基本方針と整合する。

一方、AuditLog と RelationStore のフィードバックループは入口段階にとどまる。Semantic 本格評価や制度層は Phase 1 のスコープ外として明示すべきである。

## 1. 最優先で改善すべき点

### 1.1 `run_phase1_evaluation()` の戻り値

呼び出し側が Structural Diff、SemanticDelta、RDE、Policy、Audit の各成果物を受け取れないと、UI・CLI・監査確認・将来の RelationStore 更新に支障が出る。

**推奨:** `Phase1EvaluationResult`（`structural_diff`, `semantic_delta`, `rde_result`, `policy_decision`, `audit_event | None`）を返す。

→ **実装済み:** `openayane_rde.runtime.result.Phase1EvaluationResult` と `run_phase1_evaluation()` の戻り値をこれに変更した。

### 1.2 RelationStore update の最小実装

neutral stub のみでは、過去の ΔM を次回判断へ戻す履歴参照ループが実装として成立しない。JSON / SQLite 等での最小ストアと、`update_from_audit_event` / `load_relation_context` のような API が次段の核となる。

### 1.3 `allowed_delta_m` の判定強化

「`allowed_delta_m` が空でない」ことだけでは不十分。実際の変更（`changed_nodes`、`protected_element_changes`、semantic stub のシグナル等）が許可リストに対応するかを照合し、数値変更などが許可されていない場合は `authorized_deviation` に寄せない。

## 2. 中優先度の改善点

### 2.1 JSON Schema と Pydantic の同期

仕様と実装の「Silent ΔM」を防ぐため、必須フィールド・主要 enum の整合をテストで固定する。

→ **実装済み:** `tests/unit/test_schema_model_sync.py` で各スキーマの `required` がモデルフィールドに含まれること、および一部 enum の一致を検証。

### 2.2 CI

プッシュ／PR で pytest・ruff・mypy を回す。

→ **実装済み:** `.github/workflows/ci.yml`（Python 3.11 / 3.12）。

### 2.3 AuditLog と RelationStore の責務

AuditLog は不可逆な事実記録。RelationStore は Audit から解釈された関係状態。実装でも「記録」と「解釈済み状態」を混ぜない。

## 3. 低〜中優先度の改善点

### 3.1 hash validation

`sha256:` プレフィックスと長さだけでなく、64 桁の 16 進であることを検証する。

→ **実装済み:** `AuditEvent` のバリデータで `^sha256:[a-fA-F0-9]{64}$` に統一。

### 3.2 Markdown 定義検出の拡張

`**用語**:` 形式以外の自然文定義（「Xとは」「Xは〜である」等）は Phase 2 以降で拡張を検討。

### 3.3 JSON Diff と JSON Schema の連動

コンストラクタで `required_fields` を渡す現状は Phase 1 で妥当。次は JSON Schema を入力に型・必須・追加プロパティを評価できるようにする。

## 4. 設計思想上の注意点

### 4.1 RDE 完成の誤認

Structural Diff とルール分類器が動いたことと、Semantic ΔM RDE や制度連携の完成を同一視しない。README 等では Phase 1 の境界を明記する。

### 4.2 OpenAyane 機構としての厚み

RelationStore 更新、履歴ループ、Modification Control、Safe Execution、Rollback、Human Review は Phase 1 では薄くてよいが、「OpenAyane 完了」と誤解されない表現にする。

## 5. 推奨する次の実装順序

1. ~~`Phase1EvaluationResult`~~（対応済み）
2. ~~CI workflow~~（対応済み）
3. ~~Schema / Model 同期テスト（第一段）~~（対応済み）
4. RelationStore minimal update
5. `allowed_delta_m` マッチング強化（例: `rde/authorization.py` の切り出し）
6. Long-chain drift テスト

## 6. RDE差異検証（要約）

| 区分 | 内容 |
|------|------|
| 保存 | RDE＝評価器、Policy＝機構という分離 |
| 変換 | 論文レベルのアーキテクチャは Phase 1 で Structural 中心に縮約（許容） |
| 補完 | Pydantic、JSON Schema ファイル、Audit JSONL、テスト群 |
| 未解決 | Semantic 本格、Relation 更新ループ、allowed 意味照合、Institution、Runtime、CI 以外の運用面 |
| 逸脱リスク | 「動いた＝RDE 完成」に見えること |

## 7. 結論

改善余地はあるが Phase 1 のスコープ設定は妥当である。次の一手は、分類器を単純に賢くすることより、**Audit を経由した履歴参照ループと Relation 状態の実体化**である。
