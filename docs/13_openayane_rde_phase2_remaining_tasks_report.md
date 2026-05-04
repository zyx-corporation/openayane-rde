# OpenAyane RDE Phase 2 残務レポート

## 0. 文書情報

文書名：OpenAyane RDE Phase 2 残務レポート  
対象リポジトリ：`zyx-corporation/openayane-rde`  
対象ブランチ：`main`  
確認対象コミット：`951a2bd96645a5a82f796852d0bd68994f50a2a9`  
作成日：2026-05-04  
位置づけ：Phase 2完了前の残務整理

## 1. 現状サマリ

Phase 2は、最小実装としてはほぼ成立している。

最新コミット `951a2bd96645a5a82f796852d0bd68994f50a2a9` では、前回レビューで指摘された主要修正が反映された。

実装済みの主な項目は以下である。

```text
- long-chain assert強化
- baseline vs stepwise のlong-chain観点追加
- citation fragility count修正
- multi-kind drift patterns
- self_report mismatch item totals
- relation_store_key とテスト
- RelationContextへのdrift counts追加
- allowed_delta synonym maps
- mode-based match threshold
- Policy history notes in rationale
- semantic_mode = structural_baseline
- is_stub=True の維持
- approve_with_notes の高履歴リスク時human_review昇格
```

これにより、Phase 2の中心である以下のループは最小実装として成立し始めている。

```text
Phase1EvaluationResult
  ↓
RelationStore Update
  ↓
RelationContext Loader
  ↓
Policy / RDE補正
  ↓
次回評価
```

評価としては以下である。

```text
Phase 2 Minimal 実装: 合格
Phase 2 完了判定: ほぼ完了
残務: 少数。ただし完了前に確認すべき項目あり
```

## 2. 実装済み確認

### 2.1 RelationStore更新の改善

`relation/update.py` では、単一drift patternではなく、複数のdrift patternを推定する `_infer_pattern_kinds()` が導入されている。

これにより、同一評価内で以下のような複数シグナルを同時に記録できる。

```text
- self_report_mismatch
- citation_deletion
- number_change
- definition_shift
- required_field_deletion
- signature_change
- constraint_omission
```

これは、前回の「一つのpatternに潰れて情報が失われる」問題への適切な修正である。

### 2.2 Citation fragility countの修正

`DocumentFragilityProfile.citation_break_count` は、従来の `reference_breaks` だけでなく、以下も加算対象になった。

```text
- deleted_nodes の citation / link
- protected_element_changes の citations
- reference_breaks
```

これにより、MarkdownDiffでcitation deletionが `deleted_nodes` や `protected_element_changes` に入る場合でも、document fragilityへ反映される。

### 2.3 Policy history notes

`policy/rules.py` と `policy/bridge.py` では、RelationContextに基づく履歴補正が `history_notes` として返され、`PolicyDecision.rationale` に反映されるようになった。

これにより、以下のような補正理由が監査可能になる。

```text
- generator_reliability_score <= 0.3
- review_threshold_adjustment >= 0.5
- approve_with_notes かつ高threshold
- document_fragility_score >= 0.7
```

これは、Policy判断の説明可能性を大きく改善している。

### 2.4 allowed_delta synonym maps

`rde/authorization.py` では、allowed / forbidden delta matchingにsynonym mapが追加された。

例：

```text
sentence restructuring:
  paragraph restructured
  wording
  style
  clarity
  restructured

error handling:
  try/except
  exception handling
  validation

numeric change:
  number changed
  threshold changed
  value changed
  numeric

citation removal:
  citation deleted
  reference removed
  link removed
```

これにより、文字列完全一致だけに依存していたPhase 2初期実装よりも、実用性が上がった。

### 2.5 SemanticDelta mode

`semantic/delta_engine.py` では、SemanticDeltaに `semantic_mode = "structural_baseline"` を設定し、同時に `is_stub=True` を維持している。

これは重要である。

つまり、現在のSemanticDeltaは、LLM evaluatorによる本格意味評価ではなく、StructuralDiff由来の意味候補抽出であると明示できている。

この修正により、Phase 2実装がSemantic評価完成済みであるかのように見えるリスクが軽減された。

## 3. Phase 2残務一覧

## 3.1 CI実行結果の確認

### 状況

CI workflow自体は実装済みである。

ただし、現時点で確認対象コミット `951a2bd96645a5a82f796852d0bd68994f50a2a9` に紐づくworkflow runは取得できていない。

### 残務

GitHub Actions画面で、最新コミットに対して以下が成功していることを確認する。

```text
pytest
ruff check src tests
mypy src
Python 3.11
Python 3.12
```

### 完了条件

```text
最新mainのCIがgreenである
```

## 3.2 long-chain testの最終確認

### 状況

前回レビューで指摘したlong-chain testの弱さは、コミットメッセージ上では修正済みである。

修正内容として以下が含まれている。

```text
- long-chain asserts強化
- baseline vs stepwise
```

### 残務

実ファイルで、以下を確認する。

```text
- trust < 0.5 など履歴劣化を検証しているか
- review_threshold_adjustment > 0.0 を検証しているか
- self_report_mismatch_count > 0 を検証しているか
- drift patternが想定kindで蓄積されるか
- baseline comparisonとstepwise comparisonが分離されているか
```

### 完了条件

long-chain testが、単なる実行確認ではなく、履歴蓄積の意味を検証している。

## 3.3 RelationStore JSON実装の境界明示

### 状況

JSONRelationStoreはPhase 2 minimalとして妥当である。

ただし、JSONファイルベースのため、並行書き込み、ロック、長期運用、複数プロセス利用には弱い。

### 残務

READMEまたはPhase 2仕様に以下を明記する。

```text
JSONRelationStore is a Phase 2 minimal backend.
It is not intended for concurrent production use.
SQLite backend should be considered for Phase 3 or later.
```

### 完了条件

JSONRelationStoreの位置づけが「minimal backend」として明示される。

## 3.4 allowed_delta synonym mapの拡張余地を明記

### 状況

allowed / forbidden matchingにsynonym mapが入った。

これはPhase 2として十分な前進である。

### 残務

ただし、現状は固定ルールであり、domain-specific matcherではない。以下を今後の課題として明記する。

```text
- domain-specific allowed_delta matcher
- language-aware matching
- Japanese phrase matching
- code operation matching
- optional semantic evaluator integration
```

### 完了条件

allowed_delta matchingがPhase 2 baselineであり、完全な意味照合ではないことが明記される。

## 3.5 SemanticDeltaの位置づけ確認

### 状況

`semantic_mode = "structural_baseline"` が追加され、`is_stub=True` が維持された。

これは良い修正である。

### 残務

以下をドキュメントに明記する。

```text
SemanticDelta Phase 2 is structural-baseline extraction.
It does not perform full semantic equivalence checking.
It does not use LLM evaluator by default.
```

### 完了条件

SemanticDeltaが本格意味評価ではなく、構造差分由来の意味候補抽出であると明示される。

## 3.6 Policy補正の回帰テスト確認

### 状況

Policy履歴補正は改善され、approve_with_notesも高履歴リスクではhuman_reviewへ上がる。

### 残務

以下のテストが存在することを確認する。

```text
- generator_reliability_score <= 0.3 で approve が human_reviewになる
- review_threshold_adjustment >= 0.5 で approve が human_reviewになる
- review_threshold_adjustment >= 0.7 で approve_with_notes が human_reviewになる
- document_fragility_score >= 0.7 で approve / approve_with_notes が human_reviewになる
- rationaleにHistory adjustmentが含まれる
```

### 完了条件

履歴補正とrationale記録がテストで固定される。

## 3.7 RelationContext drift count確認

### 状況

コミットメッセージ上では、RelationContextにdrift countsが追加された。

### 残務

以下を確認する。

```text
- RelationContextにdrift_pattern_countsが存在するか
- relation_record_to_context() でcountが落ちないか
- Policyまたは将来のRDE補正でcountを利用できるか
```

### 完了条件

RelationStoreRecordのdrift pattern countがRelationContextへ保持される。

## 4. 残務優先順位

### Priority 1

```text
- 最新コミットのCI green確認
- long-chain testのassert内容確認
- Policy補正テスト確認
```

理由：Phase 2完了判定に直結する。

### Priority 2

```text
- JSONRelationStore minimal backendであることをREADME/仕様に明記
- SemanticDelta structural_baselineの位置づけを明記
- allowed_delta matchingのbaseline性を明記
```

理由：過剰な完成誤認を防ぐ。

### Priority 3

```text
- RelationContext drift countの保持確認
- SQLite backendをPhase 3候補として明記
- domain-specific allowed_delta matcherをPhase 3候補として明記
```

理由：Phase 3設計への橋渡し。

## 5. Phase 2完了判定

現時点では、Phase 2はほぼ完了している。

ただし、正式に完了扱いにする前に、以下を確認することを推奨する。

```text
1. 最新mainのCIがgreen
2. long-chain testが履歴蓄積を意味的に検証している
3. Policy補正理由がrationaleに入るテストが存在する
4. JSONRelationStore / allowed_delta / SemanticDelta structural_baseline の限界が文書化されている
```

これらが満たされれば、Phase 2は完了としてよい。

## 6. RDE差異検証

### 6.1 保存された要素

RDEは評価器、OpenAyaneは機構であるという基本方針は保存されている。

RelationStore更新はRDE Core内部ではなく、Phase1EvaluationResultを受け取るOpenAyane側のrelation update層で行われている。

### 6.2 変換された要素

Phase 2仕様上の履歴参照ループは、JSONRelationStore、RelationStoreRecord、RelationUpdateSummary、RelationContext Loaderを中心とする最小実装へ変換された。

これは実装可能性を重視したAuthorized Transformationである。

### 6.3 補完された要素

以下が補完された。

```text
- multi-kind drift patterns
- self_report mismatch item totals
- relation_store_key
- drift counts on RelationContext
- allowed_delta synonym maps
- mode-based match threshold
- policy history notes in rationale
- semantic_mode structural_baseline
- stronger long-chain tests
```

### 6.4 未解決の要素

以下はPhase 2では未解決のまま残る。

```text
- CI結果の外部確認
- JSONRelationStoreの並行安全性
- SQLite backend
- domain-specific allowed_delta matcher
- full SemanticDelta / LLM evaluator
- Human Review結果によるRelation補正
- Institution Layer
```

### 6.5 逸脱リスク

Phase 2がかなり充実したため、SemanticDeltaやallowed_delta matchingが本格的意味理解に到達したように見えるリスクがある。

実際には、現在のSemanticDeltaはstructural_baselineであり、allowed_delta matchingもsynonym mapを持つルールベースである。

これを明示しないと、理論的主張が実装上の便宜へすり替わる。

### 6.6 次回方針

Phase 2の残務確認後、Phase 3として以下を検討する。

```text
- SQLiteRelationStore
- Human Review Workflow
- Agent Execution Gate
- Safe Execution Runtime
- Tool call gating
- Rollback Manager
- Optional semantic evaluator
```

## 7. 結論

Phase 2は、実装としてほぼ完了段階にある。

ただし、正式完了前に必要なのは、新機能の追加ではなく、以下の確認と明文化である。

```text
- CI green
- long-chain testの意味的強度
- Policy補正テスト
- JSONRelationStore / SemanticDelta / allowed_delta matching の限界明記
```

これらを終えれば、Phase 2は完了扱いにしてよい。
