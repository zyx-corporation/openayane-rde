---
title: "OpenAyane RDE Phase 2 仕様メモ（ドラフト）"
date: "2026-05-04"
status: "draft (baseline implementation in repo; extend per roadmap)"
---

# OpenAyane RDE Phase 2 仕様メモ（ドラフト）

Phase 1 は **Structural RDE MVP**（差分・分類・Policy・任意 Audit）までを対象とする。Phase 2 は **履歴参照ループ** と **Relation 状態の実体化**、および **Semantic ΔM の本格化** を中核に置く。本文書は Phase 1 改善レビューで挙がった残項目と、実装に向けた境界・API を整理する。

## 1. Phase 1 との境界

| 区分 | Phase 1（現状） | Phase 2（目標） |
|------|-----------------|-----------------|
| Semantic ΔM | stub（`SemanticDelta.is_stub`） | `estimate_semantic_delta` の実装・検証 |
| RelationStore | `RelationContext` の no-op 更新 | 永続ストア・読み書き API・信頼度更新式 |
| Audit | JSONL 追記・ハッシュ検証 | Audit をソースとした Relation 更新の一貫性 |
| 統合 | `run_phase1_evaluation` → `Phase1EvaluationResult` | 評価結果から Relation 更新までの単一パイプライン |

**注意:** Phase 1 の充実（CI・スキーマ同期・統合テスト）だけでは Phase 2 は完了しない。「Phase 2 に入った」と誤認されないよう、リリースノートや README の境界表現を維持する。

## 2. `Phase1EvaluationResult`（Phase 2 向けの入力単位）

`Phase1EvaluationResult` は次を束ねる。

- **入力のスナップショット:** `task_contract`, `generator_output`, 任意の `relation_context`
- **評価パイプライン:** `structural_diff`, `semantic_delta`, `rde_result`, `policy_decision`
- **任意の監査:** `audit_event`（`audit_log_path` 指定時のみ）

呼び出し側が Contract / GeneratorOutput を別引数で保持し続けなくても、**同一の評価単位**を永続化・再処理できるようにするのが目的である。

## 3. Relation 更新フック（現状スタブ）

```text
update_relation_from_evaluation_result(result: Phase1EvaluationResult) -> RelationUpdateSummary
```

- **Phase 1:** `RelationUpdateSummary.updated` は常に `false`。`update_relation_context` は実質 identity。
- **Phase 2:** `rde_result`・`audit_event`（存在時）・`relation_context` を用いた trust / stability / context_affinity の更新式をここに集約する想定。

Audit が無い実行では、監査相関 ID が無い旨を `message` に残し、入力の `RelationContext` をそのまま返す。

## 4. スキーマと実装の同期（継続）

- **必須フィールド:** 各 `schemas/*.schema.json` の `required` が Pydantic フィールドに含まれること。
- **enum:** `RDEClassification`, `RiskLevel`, `RequiredAction`, `ProtectedElementKind`, `OutputType`, `AuditActionKind`, `ProviderKind`, `DiffDomain`, `ChangeType` 等を JSON Schema の `enum` と突き合わせる（`tests/unit/test_schema_model_sync.py`）。
- **代表インスタンス:** `tests/schema_fixtures/*.valid.json` を `jsonschema` で検証し、スキーマが「実例で破綻しない」ことを CI で担保する。
- **PolicyDecision:** 現状は専用 JSON Schema が無い。`PolicyActionKind` と `RequiredAction` の一致をテストで固定している。

## 5. Phase 2 で優先する実装ブロック

1. **RelationStore 最小実装**（JSON / SQLite 等）と `load_relation_context` / `save_relation_context`。
2. **`allowed_delta_m` と構造差分の意味照合**（許可文言と実際の変更種別のマッチング）。
3. **Semantic エンジン**（stub からの置換、テスト可能なスコアリング）。
4. **Long-chain drift**（監査・Relation を跨いだ系列テスト）。

## 6. 参照

- Phase 1 改善レポート: `docs/04_openayane_rde_phase1_improvement_report.md`
- CI: `.github/workflows/ci.yml`
