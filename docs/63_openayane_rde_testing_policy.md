---
title: "OpenAyane RDE — RDE観点のテスト方針"
version: "0.1"
date: "2026-05-06"
status: "normative-guidance"
---

# RDE観点のテスト方針

## 0. 目的

本書は、OpenAyane RDE のテストを **「逸脱（ΔM）の観測・分類・監査」という設計意図**に沿って設計・保守するための方針をまとめる。汎用アプリの回帰テストだけでは足りない論点（**RDE 分類と Policy の分離**、**生成系の自己申告の非権威性**、**証拠スコープの過剰主張の防止**）を明示する。

**親文書:** [`00_development_plan.md`](00_development_plan.md) §10（特に §10.1–§10.3）。  
**追跡 Issue:** GitHub [#99](https://github.com/zyx-corporation/openayane-rde/issues/99)。

## 1. テストが固定するもの / 固定しないもの

### 1.1 固定する（望ましい）

- **契約と入力に対する RDE の出力:** `RDEResult` の分類・リスク・根拠フィールドなど、仕様で意味が定まっている振る舞い。
- **構造化された逸脱シナリオ:** TaskContract、StructuralDiff、期待する golden / benchmark 結果の対応。
- **直列化・スキーマの構造:** Pydantic モデルと `schemas/*.schema.json` の整合（`tests/unit/test_schema_*.py`）。
- **監査・関係ストアの記録形状:** AuditEvent ペイロードや RelationStore レコードの**構造**（意味的正しさの全称証明ではない）。

### 1.2 固定しない・主張してはならないもの

テストが通過したことは次を **意味しない**（[`specs/known_limitations.md`](../specs/known_limitations.md) と併読すること）。

- 任意ドメイン・任意言語・任意モデルに対する **外部有効性** や校準済み誤り率。
- **意味同値** または完全な「サイレント ΔM」検出能力。
- 本番の制度・本人性・暗号化監査としての **高保証**。

テスト名・コメント・README でこれらを暗示しないこと。

## 2. フィクスチャと golden の考え方

### 2.1 逸脱ケースを先に置く

開発計画 §10.1 の順序を守る。

```text
1. 期待される逸脱ケースを fixture 化する
2. 期待分類を golden result として定義する
3. テストを先に書く
4. 実装する
5. regression を CI で固定する
```

「正常系だけ」のテストに偏ると、RDE が本来扱う **疑わしい逸脱・重大歪曲** の回帰を拾えなくなる。

### 2.2 Golden は「正しい世界」の定義ではない

Golden / `expected_rde_result.json` は **「この契約とこの差分に対して、現行の RDE 規則が返すべき分類・ポリシー行動」** の参照実装である。仕様変更や分類語彙の拡張時は、**意図した意味変化（ΔM）**として golden 更新をレビューする。無批判な期待値の書き換えは **suspicious drift**（実装と証拠のずれ）を招く。

## 3. RDE 分類と Policy をテストで混同しない

- **RDE** は「何が起きたか」（`preserved` / `suspicious_drift` / `critical_corruption` 等）を返す。
- **Policy** は「どう扱うか」（`approve` / `halt` 等）を返す。

テストでは、可能なら **RDEResult** と **PolicyDecision** のどちらを検証しているか明示する。両方を一括で比較する場合も、コメントまたはアサーション分割で **責務の境界**が読めるようにする。Policy だけを見て RDE の分類が正しいと論じない。

## 4. Generator の自己申告とテストデータ

`SelfReport` は **補助情報**である。テストでは次を原則とする。

- 主張の根拠は **StructuralDiff / SemanticDelta（stub 含む）** 側に置く。
- 「自己申告どおりだから通過」のみを意味するケースを増やしすぎない。自己申告と差分の不一致（ミスマッチ）を **明示的なフィクスチャ**で持つ（例: Phase 6 の self-report mismatch 系）。

## 5. テストレイヤの役割分担（目安）

| レイヤ | 主な目的 | RDE 上の意味 |
|--------|-----------|----------------|
| 単体（unit） | 純粋関数・小さな不変条件 | 分類ロジック・スキーマ・型の健全性 |
| Golden（`tests/golden/`） | エンドツーエンドに近い契約通し | 期待される RDE 分類・ポリシー行動の回帰固定 |
| Benchmark（`tests/benchmarks/` / `benchmarks/`） | 研究・報告用の再現単位 | フィクスチャ集合に対する一致率；**集合外への一般化は主張しない** |
| Schema / model 同期 | JSON と Pydantic の構造一致 | **構造**の逸脱検知；意味妥当性は別問題 |

## 6. 回帰と「実装の意味変化」

CI での回帰は、**意図しない RDE 意味の変化**を検知するための安全装置である。変更が分類閾値や説明責任に影響する場合は、次をセットで満たすこと。

- 仕様または `known_limitations` の更新が必要か検討済みであること。
- Golden / benchmark の更新理由がレビューで説明できること（「テストを緑にしただけ」でないこと）。

## 7. 参照

- [`00_development_plan.md`](00_development_plan.md) §10、§14（RDE 差異検証観点）
- [`specs/rde_core_spec.md`](../specs/rde_core_spec.md)
- [`specs/known_limitations.md`](../specs/known_limitations.md)
- [`benchmarks/METRICS.md`](../benchmarks/METRICS.md)（ベンチマーク指標の非主張）
