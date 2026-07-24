---
title: "OpenAyane RDE — Post-Phase 6 プロジェクト用 Issue バックログ"
version: "0.1"
date: "2026-05-06"
status: "planning-backlog"
---

# Post-Phase 6 プロジェクト用 Issue バックログ

## 0. 目的

Phase 5・6 完了後の作業を **GitHub Project** で追いやすい粒度に分解した起票用ドラフトである。各節は **1 Issue = 1 行** 相当のスコープを想定する。

**親方針・参照:**

- テスト方針: [`63_openayane_rde_testing_policy.md`](63_openayane_rde_testing_policy.md)（追跡 [#99](https://github.com/zyx-corporation/openayane-rde/issues/99)）
- Phase 6 出口・オープン項目: [`62_openayane_rde_phase6_completion_report.md`](62_openayane_rde_phase6_completion_report.md) §5
- Phase 5 拡張候補: [`52_openayane_rde_phase5_completion_report.md`](52_openayane_rde_phase5_completion_report.md) §6
- 未解決の深いテーマ（長期）: [`00_development_plan.md`](00_development_plan.md) §14.4

## 1. GitHub Project への載せ方（推奨）

1. リポジトリまたは Organization で **Project** を新規作成（例: 「Post-Phase 6」）。
2. 下記 **Epic A / B** の各 Issue を起票し、Project の **Status** フィールドで進行管理する。
3. ラベル例（未作成なら追加）: `documentation`, `testing`, `ci`, `schema`, `api`, `adapter`, `benchmark`, `research`, `paper`。
4. **一括起票:** `gh auth login` 後に [`scripts/create_post_phase6_issues.sh`](../scripts/create_post_phase6_issues.sh) を実行（`--dry-run` でコマンドのみ表示）。

## 2. Epic A — すぐ効く（ドキュメント／品質）

| ID | 提案タイトル | 提案ラベル |
|----|----------------|------------|
| A1 | テスト監査: `RDEResult` と `PolicyDecision` の検証境界を明示化する | `testing` |
| A2 | Golden / 単体テストに `docs/63` テスト方針への参照コメントを追加する | `documentation`, `testing` |
| A3 | 自己申告ミスマッチ系フィクスチャの棚卸しと不足ケースの Issue 化 | `testing` |
| A4 | CI に `openayane-rde schema validate` と `golden run` を明示ステップとして追加する | `ci` |
| A5 | RelationStore トップレベル `schemas/relation_store.schema.json` の採用と spec 整合 | `schema`, `documentation` |
| A6 | `docs/60_openayane_rde_phase6_issue_branch_plan.md` の Issue 番号追記とメンテ方針 | `documentation` |
| A7 | CONTRIBUTING（または README）に CHANGELOG / 互換ポリシー（`docs/51`）への導線を追加する | `documentation` |

### Epic A 実施状況（依存順）

```text
A1 -> A2 -> A3 -> A4/A5 -> A6 -> A7
```

| ID | 状況 | 根拠 |
|----|------|------|
| A1 | 実施済み | `tests/golden/test_golden.py`, `tests/unit/test_rde_classifier.py`, `tests/unit/test_policy_bridge.py`, `tests/unit/test_phase1_flow.py` で RDE/Policy 境界を明示 |
| A2 | 実施済み | `tests/README.md` と上記テストモジュール先頭 docstring で `docs/63` を参照 |
| A3 | 実施済み | `benchmarks/generator_self_report_mismatch/README.md` に棚卸し表とギャップを記載 |
| A4 | 実施済み | `.github/workflows/ci.yml` に `openayane-rde schema validate` / `openayane-rde golden run` の明示ステップあり |
| A5 | 実施済み | `schemas/relation_store.schema.json` 採用済み、`tests/unit/test_schema_fixtures.py` / `tests/unit/test_schema_validation.py` で検証 |
| A6 | 実施済み | `docs/60_openayane_rde_phase6_issue_branch_plan.md` §3 と §8.6 に Issue 番号・更新方針を反映 |
| A7 | 実施済み | `CONTRIBUTING.md` を追加し、`README.md` の Contributing 節から導線を追加 |

### A1 — 本文ドラフト

```text
## 概要
`docs/63_openayane_rde_testing_policy.md` §3 に従い、既存テストで RDE 分類と Policy 行動を混同していないか棚卸しし、必要ならアサーション分割・コメントで境界を明示する。

## 完了条件
- [ ] 主要 golden / 分類テストで「何を検証しているか」が RDE / Policy のどちらか読み取れる
- [ ] 方針に反するテストがあれば修正または `known_limitations` への言及
- [ ] 関連: #99
```

### A2 — 本文ドラフト

```text
## 概要
テストファイル先頭または該当ケース付近に、`docs/63`（RDE と Policy の分離、golden の意味、自己申告の位置づけ）への短い参照を追加する。冗長にならないようモジュール単位でまとめてもよい。

## 完了条件
- [ ] `tests/golden/` および分類・ポリシーに触れる `tests/unit/` に参照が一貫してある
- [ ] 関連: #99
```

### A3 — 本文ドラフト

```text
## 概要
`docs/63` §4 に沿い、SelfReport と StructuralDiff の不一致を表すフィクスチャの有無・カバー範囲を一覧化し、不足があれば追補 Issue を切る。

## 完了条件
- [ ] 棚卸し結果がコメントまたは短い `docs/` 節（任意）に残る
- [ ] ギャップがあればフォローアップ Issue へのリンク
- [ ] 関連: #99
```

### A4 — 本文ドラフト

```text
## 概要
`.github/workflows/ci.yml` は現状 `pytest` / ruff / mypy のみ。`openayane-rde schema validate` と `golden run` を CI ステップとして明示し、CLI 回帰も固定する（既に pytest 内で同等なら、その旨を CI コメントで明文化してもよい）。

## 完了条件
- [ ] CI で schema validate と golden run が実行される、または同等カバレッジがコードコメントで説明される
- [ ] 失敗時のログがローカル再現手順と一致する
```

### A5 — 本文ドラフト

```text
## 概要
`docs/62_openayane_rde_phase6_completion_report.md` §5 にあるとおり、RelationStore 全体のトップレベル JSON Schema が未採用。`specs/relation_store_schema.md` と Pydantic / 既存スキーマ群との整合を取り、`schemas/relation_store.schema.json` を追加または更新する。

## 完了条件
- [ ] トップレベル schema がリポジトリに存在し、単体または schema テストで参照される
- [ ] spec 文書と矛盾がない
```

### A6 — 本文ドラフト

```text
## 概要
`docs/60_openayane_rde_phase6_issue_branch_plan.md` の「次回更新」方針に従い、GitHub Issue 作成済みの項目には Issue 番号を表に反映する。Phase 6 が PR スタックだった場合の扱いも一言メモする。

## 完了条件
- [ ] 計画書内の追跡表が現状と一致
- [ ] 今後の番号追記ルールが文書上明確
```

### A7 — 本文ドラフト

```text
## 概要
コントリビュータがリリース時に `docs/51_openayane_rde_release_compatibility_policy.md` と CHANGELOG を更新しやすいよう、`CONTRIBUTING.md` を新規に置くか、`README.md` に同等の短い導線とチェックリストを追加する。

## 完了条件
- [ ] 新規 PR で互換・CHANGELOG の確認が手順に含まれる
```

## 3. Epic B — 製品・研究として伸ばす候補

| ID | 提案タイトル | 提案ラベル |
|----|----------------|------------|
| B1 | API: ローカル評価用の最小 HTTP エンドポイント実装（設定で有効化） | `api` |
| B2 | API: 契約テスト・エラーレスポンス・501 からの移行方針 | `api`, `testing` |
| B3 | GitHub PR アダプタ: ライブ投稿（opt-in）の設計スパイクとリスク記録 | `adapter`, `documentation` |
| B4 | ベンチマーク: 多言語小規模フィクスチャ追加（外部主張なし） | `benchmark`, `research` |
| B5 | ベンチマーク: 敵対的／ストレス系フィクスチャの方針と初回セット | `benchmark`, `research` |
| B6 | 論文ドラフトと Phase 6 ベースライン報告の数値・図表の同期 | `paper`, `documentation` |
| B7 | `benchmarks/README`: 評価プロトコル拡張手順の明文化 | `benchmark`, `documentation` |

### B1 — 本文ドラフト

```text
## 概要
`src/openayane_rde/api/app.py` のスケルトンを超え、設定（例: openayane.toml または環境変数）で有効化される **最小** の評価 API を実装する。本番認証・高保証は対象外（`specs/known_limitations.md` 整合）。

## 完了条件
- [ ] ローカルで文書化された手順から呼び出せる
- [ ] 既定は従来どおり安全側（無効または local-only）
```

### B2 — 本文ドラフト

```text
## 概要
B1 とあわせ、ステータスコード・エラーペイロード・OpenAPI 有無を決め、契約テストで固定する。既存 501 エンドポイントの廃止／移行表を README または api モジュール doc に残す。

## 完了条件
- [ ] 契約テストが CI を通る
- [ ] 破壊的変更は `docs/51` に照らして記録
```

### B3 — 本文ドラフト

```text
## 概要
Phase 5 完了レポートの「GitHub live posting（明示 opt-in）」を前進させる前に、権限・レート制限・誤投稿リスク・監査ログとの関係を 1 本の設計メモ（`docs/`）にまとめる。実装は別 Issue でも可。

## 完了条件
- [ ] opt-in 時の脅威と非目標が明文化されている
- [ ] 実装 Issue への参照がある
```

### B4 — 本文ドラフト

```text
## 概要
`benchmarks/` に小さな多言語フィクスチャを追加し、`evaluate.py` で回せるようにする。`benchmarks/METRICS.md` に集合外一般化を主張しない旨を維持・追記する。

## 完了条件
- [ ] 新フィクスチャが評価ハーネスに載る
- [ ] 非主張スコープが文書で明確
```

### B5 — 本文ドラフト

```text
## 概要
敵対的・ストレス系（長文、境界値、意図的な schema 逸脱など）の方針を `benchmarks/README.md` または `specs/known_limitations.md` と整合させ、初回の最小セットを追加する。

## 完了条件
- [ ] 方針文書とフィクスチャが対応づけされている
- [ ] CI / evaluate で再現可能
```

### B6 — 本文ドラフト

```text
## 概要
`papers/openayane_rde_paper_draft.md` の記述を `reports/phase6_baseline_evaluation.md` および `reports/phase6_baseline_eval.json` と突合し、数値・用語・図表参照を一致させる。

## 完了条件
- [ ] 論文ドラフト内の定量・ファイル参照がレポートと矛盾しない
- [ ] 主張スコープが `known_limitations` と矛盾しない
```

### B7 — 本文ドラフト

```text
## 概要
新しいベンチマーク単位やメトリクスを追加する際の手順（ディレクトリ規約、期待 JSON、evaluate.py への登録、METRICS 更新）を `benchmarks/README.md` に追記する。

## 完了条件
- [ ] コントリビュータが手順だけで拡張できる
```

## 4. 依存関係（目安）

```text
A1 → A2（監査結果を踏まえてコメント配置が安定しやすい）
A4 は A5 と独立だが、schema 変更時は CI 順序に注意
B2 は B1 に依存
B6 は B4/B5 より先に着手可能（論文と既存 baseline の同期）
```

## 5. 重要マイルストーン記録

### M-RDE-G0: RDE pre-gateway integration baseline

本マイルストーンは、Gateway 連携前段の RDE 統合境界を固定する。

**完了条件:**

```text
- /v1/evaluate の request/response/error contract 固定
- Phase 1 structural diff evaluation が opt-in で動作
- RDE result schema が Gateway から読める
- recommended_action は返すが未執行
- benchmark report と known_limitations が更新済み
- rde-pre-gateway-integration-v0.2.0 タグを作成
```

## 6. 文書履歴

| Version | Date | Note |
|---------|------|------|
| 0.1 | 2026-05-06 | 初版（Epic A7 + B7、計 14 Issue） |
