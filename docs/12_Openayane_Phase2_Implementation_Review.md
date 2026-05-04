# OpenAyane Phase 2 実装評価・修正レポート

## 0. 評価対象

対象リポジトリ：`zyx-corporation/openayane-rde`
対象ブランチ：`main`
確認対象コミット：`46a23bc2ad5c48d7156c33abab073bee3e2cf6ea`
コミット概要：`Phase 2: RelationStore JSON, relation updates, allowed-delta matching`

本レポートは、Phase 2 詳細仕様に対して、GitHub上の最新実装がどの程度対応しているかを確認し、改善点を整理するものである。

## 1. 総合評価

Phase 2実装は、**履歴参照ループの最小実体化**としてかなり良い到達点にある。

Phase 1では、StructuralDiff、SemanticDelta stub、RDEResult、PolicyDecision、AuditEventを束ねる `Phase1EvaluationResult` が成立した。Phase 2では、それをRelationStoreへ流す実装が追加され、OpenAyaneが単発評価器の周辺実装から、履歴を持つ意味変化監査機構へ進み始めた。

評価としては以下である。

```text
Phase 2 Minimal Relation Feedback 実装評価: 85〜90点
```

主な達成点は以下である。

```text
- JSONRelationStoreが実装された
- RelationStoreRecord / DriftPattern / GeneratorReliabilityProfile / DocumentFragilityProfile が追加された
- update_relation_from_evaluation_result() が実処理化された
- AuditEventがある場合のみRelationStoreを更新するOption Aが実装された
- RelationContext LoaderがRelationStoreから実データを返せるようになった
- allowed_delta_m / forbidden_delta_m matchingが導入された
- RDE classifierがallowed_delta_m matchingを参照するようになった
- Policy BridgeがRelationContextに基づいてapproveをhuman_reviewへ補正できるようになった
- SemanticDeltaEngineがStructuralDiff由来の意味候補抽出へ拡張された
- long-chain drift testが追加された
```

ただし、Phase 2全体が完了したとまでは言い切れない。現時点では、Phase 2の中核部品は実装されたが、Relation更新ロジック、drift pattern分類、allowed_delta_m matching、long-chain testの強度には改善余地がある。

## 2. Phase 2仕様との対応

## 2.1 RelationStore minimal

### 評価

合格。

`RelationStore` Protocolと `JSONRelationStore` が実装されている。`get()`、`upsert()`、`load_context()` を持ち、JSONファイルへの保存もatomic writeに近い形で一時ファイル経由になっている。

```text
RelationStore:
  get(subject_id, object_id)
  upsert(record)
  load_context(subject_id, object_id)
```

この構成はPhase 2 minimalとして妥当である。

### 良い点

* ProtocolとしてRelationStore境界を切っている
* JSONRelationStoreを最小永続層として実装している
* `load_context()` がRelationContext Loaderへ接続している
* 保存形式がPydanticの `model_dump(mode="json")` によってJSON化されている

### 改善点

現状のstore keyは `subject_id + \x1f + object_id` で作られている。実用上は問題ないが、将来のデバッグ性を考えると、store内部でキー生成規則を明示し、テストも追加した方がよい。

また、並行書き込みへの耐性はまだ限定的である。Phase 2 minimalでは許容できるが、Phase 3以降でSQLite移行を検討すべきである。

## 2.2 RelationStoreRecordと関係プロファイル

### 評価

合格。

モデルには、`RelationStoreRecord`、`DriftPattern`、`GeneratorReliabilityProfile`、`DocumentFragilityProfile`、`AllowedDeltaMatchResult`、拡張 `RelationUpdateSummary` が追加されている。

これはPhase 2仕様とよく整合している。

### 良い点

`RelationStoreRecord` は、以下を保持する。

```text
- trust
- stability
- context_affinity
- interaction_count
- critical_corruption_count
- suspicious_drift_count
- self_report_mismatch_count
- drift_patterns
- generator_reliability_profile
- document_fragility_profile
- review_threshold_adjustment
- last_delta_m
- last_audit_event_id
```

これにより、履歴参照ループの状態保持が可能になった。

### 改善点

`RelationStoreRecord` の `relation_type` は初期値 `generator-document` でよいが、現在の `update_relation_from_evaluation_result()` では、relation_typeを文脈から推定していない。将来的には、TaskContractのmodeやtarget_scope、GeneratorOutputのproviderなどからrelation_typeを明示的に設定した方がよい。

## 2.3 update_relation_from_evaluation_result()

### 評価

合格。ただし更新ロジックはPhase 2初期実装として保守的に扱うべきである。

`update_relation_from_evaluation_result()` は、Phase 2仕様に沿って `Phase1EvaluationResult` を入力とし、RelationStoreが与えられ、かつAuditEventが存在する場合のみ永続更新を行う。

これは「AuditEventがある評価のみRelationStore更新対象」とするOption Aに合致している。

### 良い点

* AuditEventがない場合は更新しない
* storeがない場合はin-memory hook扱いに留める
* `trust_before` / `trust_after` などの差分情報を `RelationUpdateSummary` に返す
* `last_audit_event_id` を記録する
* `Phase1EvaluationResult` から再評価なしに必要情報を取得している

### 改善点

#### 2.3.1 self_report_mismatch_count がイベント数ではなく評価回数単位になっている

現在、self_report_mismatchが1件以上あれば `self_report_mismatch_count += 1` となっているように見える。これは「mismatch発生評価回数」を数えるなら妥当だが、「mismatch件数」を数えるなら不十分である。

仕様上、どちらを数えるのかを明確化すべきである。

推奨：

```text
self_report_mismatch_event_count:
  self-report mismatchを含んだ評価回数

self_report_mismatch_item_count:
  mismatch項目数の累計
```

Phase 2では前者だけでもよいが、名前を明確にすることが望ましい。

#### 2.3.2 citation_break_countがreference_breaksに依存している

DocumentFragilityProfileの `citation_break_count` 更新が `structural_diff.reference_breaks` に依存しているが、MarkdownDiffではcitation deletionが `deleted_nodes` と `protected_element_changes` に入り、`reference_breaks` には入っていない可能性がある。

その場合、citation削除を検出しているにもかかわらず、document_fragility_profileの `citation_break_count` に反映されない。

修正案：

```python
citation_changes = sum(
    1 for n in structural_diff.deleted_nodes
    if n.kind in ("citation", "link")
)
profile.citation_break_count += citation_changes
```

さらに、protected_element_changesの `element == "citations"` も加味する。

#### 2.3.3 drift patternが常にotherを含みやすい可能性

`_infer_pattern_kind()` は一つのkindを返す設計である。self-report mismatchがある場合は最初に `self_report_mismatch` になるため、同じ評価内でnumber_changeやcitation_deletionがあっても、主要patternとしてはself_report_mismatchだけが記録される可能性がある。

これは設計としては単純だが、drift patternの多重性を失う。

Phase 2改善案：

```python
def infer_pattern_kinds(...) -> list[DriftPatternKind]:
    ...
```

1評価で複数patternを更新できるようにする。

## 2.4 RelationContext Loader

### 評価

合格。

`relation_record_to_context()` により、RelationStoreRecordからRelationContextへ射影できるようになっている。

以下がRelationContextへ入る。

```text
- trust
- stability
- context_affinity
- interaction_count
- last_delta_m
- drift_patterns
- review_threshold_adjustment
- generator_reliability_score
- document_fragility_score
- last_updated_at
```

これはPhase 2仕様と整合している。

### 改善点

`drift_patterns` が `list[str]` へ変換されているため、countやseverityがRelationContext側では失われる。Policy補正で「同一drift patternが3回以上」という判定をするなら、RelationContextにもcountまたはsummaryを渡す必要がある。

修正案：

```python
class RelationContext(BaseModel):
    drift_patterns: list[str]
    drift_pattern_counts: dict[str, int] = Field(default_factory=dict)
```

または、RelationContextに `drift_pattern_summary` を追加する。

## 2.5 allowed_delta_m matching

### 評価

部分合格。

`match_allowed_delta()` が追加され、RDE classifierがこれを参照するようになった。これは前回指摘した「allowed_delta_mが存在するだけでauthorized_deviationに寄る」問題への対応であり、方向性は正しい。

### 良い点

* `changed_nodes`、`deleted_nodes`、`added_nodes`、`protected_element_changes`、`schema_violations`、SemanticDeltaの各changed_*を照合対象にしている
* forbidden phrase hitを明示的に検出している
* protected changeをunmatched扱いにしている
* match_scoreが低い場合、authorized_deviationからsuspicious_driftへ落とす設計になっている

### 改善点

#### 2.5.1 文字列完全包含に依存しすぎている

現在は、allowed_delta_mやforbidden_delta_mのフレーズがdiff descriptionに含まれるかで判定している。これはMVPとしてはよいが、かなり脆い。

例：

```text
allowed_delta_m:
  sentence restructuring

diff description:
  Paragraph restructured.
```

この場合、意味的には一致していても、文字列としては一致しない可能性がある。

Phase 2内で改善するなら、簡易synonym mapを導入するとよい。

```python
_ALLOWED_SYNONYMS = {
    "sentence restructuring": ["paragraph restructured", "wording", "style", "clarity"],
    "error handling": ["try/except", "exception handling", "validation"],
    "redundancy removal": ["redundant", "duplication", "shortened"],
}
```

#### 2.5.2 forbidden_delta_mも同様に正規化が必要

`numeric change` と `number changed`、`citation removal` と `citation deleted` のような差異を扱う必要がある。

## 2.6 RDE classifier統合

### 評価

合格。

Classifierが `SemanticDelta` を受け取り、`match_allowed_delta()` を呼ぶ構成になっている。forbidden matchがあればsuspicious_driftへ送り、match_scoreが低ければauthorized_deviationにしないという方針は妥当である。

### 改善点

`auth_match.match_score < 0.25` という閾値は固定値であり、根拠はまだ弱い。Phase 2では暫定でよいが、定数化してPolicy ProfileやTaskContract modeで変えられるようにするとよい。

```python
MIN_ALLOWED_DELTA_MATCH_SCORE = 0.25
```

また、research / creative modeでは閾値を下げ、preservation / execution modeでは閾値を上げる設計が望ましい。

## 2.7 Policy Bridge 履歴補正

### 評価

方向性は合格。ただし呼び出し経路をさらに確認・強化する必要がある。

Policy rulesでは、RelationContextに基づいて以下を行っている。

```text
- generator_reliability_score <= 0.3 なら approve を human_reviewへ
- review_threshold_adjustment >= 0.5 なら approve を human_reviewへ
- document_fragility_score >= 0.7 なら approve を human_reviewへ
```

これはRDE本体ではなくPolicy側で履歴補正を行う方針に合っている。

### 良い点

RDEの評価器性を保ったまま、OpenAyane機構として実行判断を保守側へ補正している。

### 改善点

#### 2.7.1 approve_with_notesは補正対象外

現在の補正は主に `action == "approve"` の場合にhuman_reviewへ上げている。だが、実用上は `approve_with_notes` も高リスク履歴ではhuman_reviewへ上げるべき場合がある。

修正案：

```python
if action in ("approve", "approve_with_notes") and high_history_risk:
    return "human_review"
```

ただし、過剰停止を避けるため、最初は `review_threshold_adjustment >= 0.7` など少し高めの閾値でもよい。

#### 2.7.2 rationaleに履歴補正理由が入らない

`decide_policy()` のrationaleは、RDE分類、risk level、Policy actionを説明するが、RelationContextによってactionが補正された場合、その理由が明示されない。

これはAudit上の透明性を損なう。

修正案：

```text
Policy action changed to human_review because generator_reliability_score <= 0.3.
```

をrationaleに含める。

## 2.8 SemanticDeltaEngine Phase 2

### 評価

部分合格。

`estimate_semantic_delta()` は、従来のstub出力を受け取り、StructuralDiffのdomainごとにchanged_claims、changed_constraints、changed_safety_conditionsを補完する構成になっている。

### 良い点

* Markdown heading deletionをclaim候補にしている
* JSON schema violationをconstraint / safety候補にしている
* Python signature changeをconstraint候補にしている
* test deletionやexception handling removalをsafety候補にしている
* LLM evaluatorに依存しないPhase 2基盤になっている

### 改善点

#### 2.8.1 ファイル名・docstringにstubの語が残っている

`semantic/stub.py` はPhase 1 stubとして残っており、`delta_engine.py` がそれを拡張している。構造としてはよいが、Phase 2では「stub + enhancer」なのか「baseline extractor」なのかを明確にすべきである。

修正案：

```text
semantic/stub.py
  -> semantic/baseline.py
```

またはdocstringで以下を明記する。

```text
Phase 2 still uses Phase 1 baseline scoring, then enriches structural semantic candidates.
```

#### 2.8.2 is_stub=Falseの意味が少し強い

`delta.is_stub = False` になっているが、実際にはLLMなし・構造差分由来の簡易抽出である。`is_stub=False` とすると、本格SemanticDeltaが実装済みに見える可能性がある。

修正案：

```python
semantic_delta_mode: Literal["stub", "structural_baseline", "llm_evaluator"]
```

またはPhase 2では `is_stub` を残しつつ、`metadata["semantic_mode"] = "structural_baseline"` を入れる。

## 2.9 Long-chain drift test

### 評価

存在は合格。ただしテスト強度は弱い。

20回のMarkdown numeric drift chain testが追加されている。RelationStoreを使い、AuditLogを生成し、`update_relation_from_evaluation_result()` を回している点は非常に良い。

### 良い点

* 20回の連鎖評価を実行している
* RelationContextを更新しながら次回へ渡している
* RelationStoreに最終状態が保存されることを確認している
* drift_patternsが1件以上になることを確認している

### 改善点

現在の受け入れ基準が弱い。

```python
assert final.review_threshold_adjustment >= 0.0
```

これは常に成立しやすく、drift蓄積を検証していない。

本来は以下を確認すべきである。

```python
assert final.review_threshold_adjustment > 0.0
assert final.self_report_mismatch_count > 0
assert final.interaction_count == 20
assert any(p.kind == "number_change" or p.kind == "self_report_mismatch" for p in final.drift_patterns)
assert final.trust < 0.5
```

ただし、現在の分類がcritical_corruption / suspicious_driftのどちらに寄るかに応じて閾値は調整すべきである。

また、テスト内で毎回 `original=text` として比較しており、前回版から次回版への差分ではなく、初期文書から各生成版への差分になっている。これは「累積drift検出」としては一つの設計だが、long-chain編集の現実に近づけるなら以下の2系統を分けるべきである。

```text
baseline comparison:
  original vs version_n

stepwise comparison:
  version_{n-1} vs version_n
```

Phase 2では、少なくとも両方のテストを用意するとよい。

## 3. 仕様との対応表

| Phase 2要件                                  | 実装状況 | 評価   |
| ------------------------------------------ | ---: | ---- |
| Phase1EvaluationResultを入力単位にする             | 実装済み | 合格   |
| RelationStore minimal                      | 実装済み | 合格   |
| JSONRelationStore                          | 実装済み | 合格   |
| update_relation_from_evaluation_result実処理化 | 実装済み | 合格   |
| AuditEventありのみ更新                           | 実装済み | 合格   |
| RelationContext Loader実データ対応               | 実装済み | 合格   |
| allowed_delta_m matching                   | 実装済み | 部分合格 |
| RDE classifier統合                           | 実装済み | 合格   |
| Policy履歴補正                                 | 実装済み | 部分合格 |
| SemanticDeltaEngine Phase 2                | 実装済み | 部分合格 |
| long-chain drift test                      | 実装済み | 部分合格 |
| CI維持                                       | 実装済み | 合格   |

## 4. 優先修正リスト

### Priority 1: long-chain testの強化

現状のlong-chain testは存在確認としては良いが、drift蓄積を十分に検証していない。

修正内容：

```text
- review_threshold_adjustment > 0.0 を検証
- trust < 0.5 を検証
- self_report_mismatch_count > 0 を検証
- number_change または self_report_mismatch pattern を検証
- baseline comparison と stepwise comparison を分ける
```

### Priority 2: DocumentFragilityProfileのcitation count修正

`citation_break_count` が `reference_breaks` だけに依存している場合、Markdown citation deletionが反映されない可能性がある。

修正内容：

```text
- deleted_nodes kind == citation をcitation_break_countへ反映
- protected_element_changes element == citations をcitation_break_countへ反映
```

### Priority 3: RelationContextにdrift pattern countを渡す

現在はRelationContextの `drift_patterns` が文字列listであり、countやseverityが失われる。

修正内容：

```python
class RelationContext(BaseModel):
    drift_patterns: list[str]
    drift_pattern_counts: dict[str, int] = Field(default_factory=dict)
```

### Priority 4: Policy補正の説明をrationaleに入れる

履歴補正でhuman_reviewへ変更された場合、その理由をPolicyDecision.rationaleに残す。

修正内容：

```text
- generator_reliability_scoreによる補正
- review_threshold_adjustmentによる補正
- document_fragility_scoreによる補正
```

### Priority 5: allowed_delta_m matchingにsynonym mapを導入

文字列完全一致だけでは脆い。

修正内容：

```text
- sentence restructuring -> paragraph restructured / wording / clarity
- error handling -> try/except / exception handling / validation
- numeric change -> number changed / threshold changed / value changed
- citation removal -> citation deleted / reference removed
```

### Priority 6: SemanticDeltaのモード表現を追加

`is_stub=False` はやや強い。

修正内容：

```python
semantic_delta_mode: Literal["stub", "structural_baseline", "llm_evaluator"]
```

またはmetadataで管理する。

## 5. RDE差異検証

### 5.1 保存された要素

RDEは評価器、OpenAyaneは機構という基本構造は保存されている。RDEはRelationStoreを直接更新せず、Phase1EvaluationResultを介してOpenAyane機構側がRelationStoreを更新している。

また、AuditEventがある評価のみRelationStoreを更新する方針により、監査可能性を優先する設計も保存されている。

### 5.2 変換された要素

Phase 2仕様で想定した履歴参照ループは、JSONRelationStoreとRelationUpdateSummaryを中心とした最小実装へ変換された。

これは本格制度層ではないが、Phase 2としては妥当なAuthorized Transformationである。

### 5.3 補完された要素

以下が補完された。

```text
- JSONRelationStore
- RelationStore Protocol
- RelationStoreRecord
- DriftPattern
- GeneratorReliabilityProfile
- DocumentFragilityProfile
- allowed_delta_m matching
- Policy履歴補正
- SemanticDelta構造候補抽出
- long-chain drift test
```

### 5.4 未解決の要素

以下は未解決である。

```text
- drift patternの多重分類
- long-chain testの強度不足
- allowed_delta_m matchingの語彙ゆらぎ対応
- Policy補正理由のAudit可能化
- SemanticDelta modeの明示化
- SQLiteまたは並行安全なRelationStore
- Human Review結果によるRelation補正
```

### 5.5 逸脱リスク

Phase 2実装により、履歴参照ループが動き始めたように見える。しかし、現状はまだ保守的なルールベース更新であり、context_affinityやstabilityの理論的更新式は未完成である。

また、`is_stub=False` によりSemanticDeltaが本格実装されたように見える危険がある。実際には、StructuralDiff由来の意味候補抽出であり、LLM evaluatorや深い意味照合ではない。

### 5.6 次回修正方針

次回修正では、まずテストの強度を上げる。

```text
1. long-chain testのassert強化
2. citation_break_count更新の修正
3. PolicyDecision rationaleに履歴補正理由を入れる
4. allowed_delta_m synonym map導入
5. SemanticDelta mode追加
```

## 6. 結論

Phase 2実装は、OpenAyaneを単発評価ループから履歴参照ループへ進めるという目的に対して、十分に前進している。

特に、JSONRelationStore、update_relation_from_evaluation_result、RelationContext Loader、Policy履歴補正、allowed_delta_m matching、SemanticDelta構造候補抽出、long-chain drift testが一通り入ったことは大きい。

ただし、Phase 2完了とするには、long-chain testの強度、drift pattern分類、Policy補正の説明可能性、SemanticDelta modeの明示化をもう一段修正した方がよい。

現時点の評価は以下である。

```text
Phase 2 Minimal 実装: 合格
Phase 2 完了判定: 条件付き未完了
```

次の修正を入れれば、Phase 2を完了扱いにかなり近づけられる。
