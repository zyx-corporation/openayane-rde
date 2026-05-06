---
title: "OpenAyane RDE Phase 6 完了レポート"
version: "0.1"
date: "2026-05-06"
status: "completion-record"
---

# OpenAyane RDE Phase 6 完了レポート

## 0. 目的

本書は **Phase 6: Research Evaluation and Public Specification**（`docs/00_development_plan.md` / `docs/60_openayane_rde_phase6_issue_branch_plan.md`）の到達点を出口記録として固定する。

- 公開可能な用語・スキーマ叙述・ベンチマーク・評価ハーネス・ベースライン報告・限界の明文化を一覧する。
- 実装証拠（テスト・フィクスチャ・レポート）と**外部主張**の境界を維持する。

**正典（計画）:** [`60_openayane_rde_phase6_issue_branch_plan.md`](60_openayane_rde_phase6_issue_branch_plan.md)。

## 1. 完了宣言

```text
Phase 6 ステータス: P6-1〜P6-7 および P6-9 / P6-8 / P6-10 の成果物をリポジトリに反映
性質: 研究・仕様・再現可能な評価アーティファクト（本番能力の拡張フェーズではない）
外部有効性の主張: なし（benchmarks/ と reports/ のスコープに限定）
```

## 2. Issue / PR 対応表（`main` へのマージ記録）

Phase 6 は **Issue なし・PR スタック**で納品した（必要なら後から Issue を遡及リンク）。**Issue** 列は未作成のため「—」とする。

| P6 | 内容 | マージに使った head ブランチ（例） | Issue | PR（`main` へ squash マージ） |
|----|------|-----------------------------------|-------|-------------------------------|
| P6-1 | RDE Core 公開仕様 | `phase6/p6-1-p6-2-core-and-schema-specs` | — | [#84](https://github.com/zyx-corporation/openayane-rde/pull/84) |
| P6-2 | スキーマ叙述 | （P6-1 と同一 PR に同梱） | — | [#84](https://github.com/zyx-corporation/openayane-rde/pull/84) |
| P6-3 | benchmark 骨格 | `phase6/p6-3-benchmark-skeleton` | — | [#91](https://github.com/zyx-corporation/openayane-rde/pull/91)（[#85](https://github.com/zyx-corporation/openayane-rde/pull/85) はベースブランチ削除で自動クローズ後、スタック復旧で再作成） |
| P6-4 | 構造ベンチマーク | `phase6/p6-4-structural-benchmark-fixtures` | — | [#86](https://github.com/zyx-corporation/openayane-rde/pull/86) |
| P6-5 | 長鎖・自己申告不一致 | `phase6/p6-5-long-chain-self-report-benchmarks` | — | [#87](https://github.com/zyx-corporation/openayane-rde/pull/87) |
| P6-6 | 評価メトリクス・`evaluate.py` | `phase6/p6-6-evaluation-metrics-harness` | — | [#88](https://github.com/zyx-corporation/openayane-rde/pull/88) |
| P6-7 | ベースライン評価レポート | `phase6/p6-7-baseline-evaluation-report` | — | [#89](https://github.com/zyx-corporation/openayane-rde/pull/89) |
| P6-9 | 既知の限界 | `phase6/p6-9-p6-8-p6-10-completion-docs` | — | [#90](https://github.com/zyx-corporation/openayane-rde/pull/90) |
| P6-8 | 技術報告スケルトン | （P6-9/10 と同一 PR） | — | [#90](https://github.com/zyx-corporation/openayane-rde/pull/90) |
| P6-10 | 本書（完了レポート） | 同上 | — | [#90](https://github.com/zyx-corporation/openayane-rde/pull/90) |

**参考:** 重複 PR [#83](https://github.com/zyx-corporation/openayane-rde/pull/83) は [#84](https://github.com/zyx-corporation/openayane-rde/pull/84) に取って代わられクローズ。

## 3. 成果物一覧

| 種別 | パス |
|------|------|
| RDE Core 仕様 | `specs/rde_core_spec.md` |
| スキーマ叙述 | `specs/task_contract_schema.md`, `specs/rde_result_schema.md`, `specs/audit_event_schema.md`, `specs/relation_store_schema.md` |
| 既知の限界・非主張 | `specs/known_limitations.md` |
| ベンチマーク README / メトリクス | `benchmarks/README.md`, `benchmarks/METRICS.md` |
| 評価スクリプト | `benchmarks/evaluate.py` |
| フィクスチャ | `benchmarks/markdown_drift/`, `json_schema_corruption/`, `python_api_drift/`, `long_chain_document_corruption/`, `generator_self_report_mismatch/` |
| テスト | `tests/benchmarks/*.py` |
| ベースライン報告 | `reports/phase6_baseline_evaluation.md`, `reports/phase6_baseline_eval.json` |
| perf サンプル | `reports/phase6_perf_sample.json` |
| 論文・技術報告ドラフト骨格 | `papers/openayane_rde_paper_draft.md` |
| Phase 6 計画 | `docs/60_openayane_rde_phase6_issue_branch_plan.md` |

## 4. ベンチマーク・評価サマリ

- **評価単位数:** 7（`benchmarks/evaluate.py` が検出する単位；長鎖はステップごとに 1 単位）。
- **ベースライン記録時の実装コミット:** `reports/phase6_baseline_eval.json` 内の `git_commit` を正とする（ドキュメントのみの後続コミットより手前の実装スナップショットを指す場合がある）。
- **直近の集計（記録時点）:** 分類・policy action・（期待 JSON に `risk_level` がある場合の）リスク一致はいずれも **7/7**。不一致が出た場合は `evaluate.py` が非ゼロ終了し、本レポートと `reports/phase6_baseline_evaluation.md` を更新すること。

詳細は **`reports/phase6_baseline_evaluation.md`** および **`benchmarks/METRICS.md`**。

## 5. 残る限界・オープン項目

- **カバレッジ:** フィクスチャは小規模・英語中心・ルールベース評価が主。大規模コーパス・多言語・敵対的評価は未着手。
- **主張の境界:** `specs/known_limitations.md` に高保証・意味同値・本番本人性・外挿の非主張を明記。
- **JSON Schema:** RelationStore 全体のトップレベル `schemas/relation_store.schema.json` は未採用（`specs/relation_store_schema.md` 参照）。
- **Issue 番号:** `docs/60_...` の「次回更新」方針に従い、GitHub Issue 作成後に計画書の表へ番号を反映すること。

## 6. Phase 7 以降・公開手続き

`docs/00_development_plan.md` の **§9.5（Phase 6 出口基準）** および **§9.6（Phase 7 トラック 7A–7D）** を正とする。Phase 6 完了境界の外の作業は、仕様硬化（7A）、評価拡張（7B）、研究・公開（7C）、制度・本番（7D）に分けて Issue 化する。

補足として、次も従来どおり別トラックの論点になりうる。

- カメラレディ論文・外部ベンチマーク・ユーザ研究（主張スコープを明示したうえで）。
- 制度・運用での実地試験（`Operational Pilot Ready` を超える場合は仕様・非主張の再検討）。
- 公開仕様の版管理（セマンティックバージョン・互換ポリシーとの整合）。

## 7. 参照

- 開発計画: [`00_development_plan.md`](00_development_plan.md)
- Phase 6 実行計画: [`60_openayane_rde_phase6_issue_branch_plan.md`](60_openayane_rde_phase6_issue_branch_plan.md)
- Phase 5 出口: [`52_openayane_rde_phase5_completion_report.md`](52_openayane_rde_phase5_completion_report.md)
- 限界: [`../specs/known_limitations.md`](../specs/known_limitations.md)
- 技術ドラフト: [`../papers/openayane_rde_paper_draft.md`](../papers/openayane_rde_paper_draft.md)
