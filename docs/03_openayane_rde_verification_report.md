---
title: "OpenAyane / RDE ドキュメント検証レポート"
version: "0.1-draft"
date: "2026-05-04"
author: "Tomoyuki Kano"
status: "verification draft"
---

# OpenAyane / RDE ドキュメント検証レポート

## 0. 検証対象

本レポートは、次の2文書を検証する。

1. OpenAyane / RDE 設計思想ドキュメント
2. OpenAyane 基本設計ドキュメント

検証観点は以下である。

- ここまでの議論を反映しているか
- OpenAyane既存設計と整合しているか
- RDEがDiff、Policy、LLM Evaluatorに矮小化されていないか
- Structural Diffの役割が正しく位置づけられているか
- Generatorへのシステムプロンプト組み込みが正しく扱われているか
- Ayane実装へ戻せる粒度になっているか
- 未解決問題を隠していないか

## 1. 議論から抽出された要求

ここまでの議論から、RDE / OpenAyane文書に反映すべき要求は次のとおりである。

```text
R1. LLMは保存ではなく再生成するため、Silent ΔMが発生する。
R2. これは単なる誤差ではなく、意味再構成の性質として扱う。
R3. 壊れること自体は悪ではない。問題は無署名の変化である。
R4. 創造的逸脱と意味腐食を区別する必要がある。
R5. 許可された変換と実際の変換の差異は、完全には検出できないが、構造化により検出可能性を高められる。
R6. Structural Diffは意味判定そのものではなく、RDEが働くための構造化レンズである。
R7. GeneratorにはRDEが働きやすいプロンプトを組み込むべきだが、Generatorを信頼してはならない。
R8. Generatorの自己申告と実diffの差分は、重要な危険信号である。
R9. RDEはOpenAyaneの設計経験から抽出し、論理的に精緻化した後、Ayane実装へ戻す。
R10. RDEはvalidator、diff checker、policy filter、LLM evaluatorではなく、意味逸脱評価構造である。
R11. OpenAyaneではrelation_store、trust、stability、context_affinity、Structor、Policy、Auditに接続する。
R12. 実装は段階的に行う。まずMarkdown/JSON/PythonのStructural Diffから始める。
```

## 2. 設計思想ドキュメントの検証

### 2.1 RDEの定義

検証結果: 合格。

設計思想ドキュメントでは、RDEを「生成系が生む意味逸脱を、許可された変化と危険な腐食に分離する評価構造」と定義している。これは、RDEを単なる差分検査やPolicy filterではなく、意味変化の裁定構造として位置づけており、議論の核心に合致する。

### 2.2 OpenAyaneからの抽出経路

検証結果: 合格。

文書は、OpenAyaneの設計経験からRDEを抽出し、その後Ayane実装へ戻すという経路を明示している。

```text
OpenAyane の設計経験
  ↓
関係・意味変化・構造評価・制度的制約の抽象化
  ↓
RDE 概念の確立
  ↓
Ayane / OpenAyane 実装への再導入
```

これは、ユーザーが明示した「まず概念を確立し、実装としてAyaneに戻す」という方針と整合する。

### 2.3 Structural Diffの位置づけ

検証結果: 合格。

文書は、Structural DiffをRDEそのものとはせず、「意味逸脱を検出可能な形に落とす構造化レンズ」として定義している。これにより、Structural Diffを過大評価せず、Semantic DiffおよびRDEの前段として適切に配置している。

### 2.4 創造性と破壊の扱い

検証結果: 合格。

文書は、変化を一律に悪とせず、Preserved、Authorized Deviation、Benign Incidental Drift、Suspicious Drift、Critical Corruption、Creative Deviationに分類している。これは、「壊れることは本当に悪か」「創造性＝破壊でもあるのではないか」という問いに対応している。

### 2.5 Generatorプロンプトの扱い

検証結果: 合格。

文書は、Generatorに変更レポートを出させるが、その自己申告を真とは見なさないと明記している。特に「実際の差分 - 自己申告差分 = 認識されていない逸脱」という観点は、RDE実装上の重要な検出信号として適切である。

### 2.6 未解決問題の扱い

検証結果: 一部改善余地あり。

設計思想文書では、完全検出不能性や非目標を明記しているが、context_affinity、value alignment、Institution Layerとの関係は基本設計文書に比べると簡潔である。将来的には、設計思想文書にも「制度的未完性」として独立節を追加するとよい。

## 3. 基本設計ドキュメントの検証

### 3.1 実装可能性

検証結果: 合格。

基本設計文書は、Intent Parser、Task Contract Builder、Generator Adapter、Structural Diff Engine、Semantic Delta Engine、RDE Core、Policy Bridge、Modification Control Flow、Safe Execution Runtime、Relation Store、Audit Engineを定義している。これはOpenAyane既存設計のモジュール群と整合しており、実装へ落とせる粒度である。

### 3.2 RDE中心アーキテクチャ

検証結果: 合格。

RDEは、GeneratorとPolicyの間に配置されている。

```text
Generator Output or Patch
  ↓
Structural Diff Engine
  ↓
Semantic Delta Engine
  ↓
RDE Core
  ↓
Policy Bridge
```

この配置は、RDEをPolicyの下位部品にせず、Policyが扱える意味変化情報を生成する中間評価層として位置づけている。

### 3.3 RelationStoreとの接続

検証結果: 合格。

RDE結果をtrust、stability、context_affinityへ戻す設計になっている。これは、OpenAyaneの「関係を時間積分された意味変化として扱う」という既存思想と一致する。

### 3.4 非機能要件

検証結果: 合格。ただし要注意。

Core処理のレイテンシ目標として<10msを掲げ、embedding生成やLLM semantic evaluationを除外している点は現実的である。ただし、RDE全体のユーザー体感レイテンシは非同期処理やキャッシュ設計に強く依存する。Phase 1ではCore判定とheavy evaluationを明確に分離する必要がある。

### 3.5 Phase設計

検証結果: 合格。

Phase 1をMarkdown/JSON/Pythonに限定している点は妥当である。これらはStructural Diffを実装しやすく、RDEの価値を早期に検証できる。

### 3.6 テスト戦略

検証結果: 合格。

Unit、Golden、Adversarial、Long-chain、Human Review Calibrationが定義されており、RDEの目的に合っている。特にGenerator self_reportが嘘をつくケースをAdversarial Testに入れている点は重要である。

## 4. 既存OpenAyane文書との整合性

### 4.1 Relation-based control layerとの整合

既存OpenAyaneは、関係状態に基づいて実行を条件づけるmeaning dynamics layerとして定義されている。今回の基本設計は、その関係状態の入力としてRDE結果を追加するものであり、既存構造を破壊しない。

### 4.2 Structorとの整合

既存OpenAyaneではStructorが生成された思考構造を評価する。今回の設計では、Structorはツール実行前やAgent planの構造評価として残し、RDEは変換前後の意味逸脱評価として位置づける。役割分担は明確である。

```text
Structor:
  実行前の思考・計画構造を評価する

RDE:
  変換前後の意味差分を評価する
```

### 4.3 Policyとの整合

既存OpenAyaneのPolicy層は実行条件を扱う。今回の設計では、RDEがPolicyに渡す意味的証拠を生成する。PolicyはRDE結果に基づき、approve、review、halt、rollbackを決定する。これは自然な拡張である。

### 4.4 Institution Layerとの整合

既存文書ではInstitution Layerが未確定の課題として残っている。今回の文書でもInstitution Layerを最終的な規範的根拠として扱い、内部Policyの限界を認めている。矛盾はない。

## 5. 潜在的矛盾と修正提案

### 5.1 RDEとResonance Gateの関係

潜在的問題:

RDEとresonance gateが混同される可能性がある。

整理:

```text
RDE:
  意味逸脱を評価・分類する構造

Resonance Gate:
  relation_stateやPolicy条件を用いて実行可否を決めるゲート
```

修正提案:

基本設計文書に「RDE is not the gate itself; it produces evidence for the gate」という注記を追加するとよい。

### 5.2 RDEとPolicyの境界

潜在的問題:

RDEがrequired_actionを返すため、Policyと重複するように見える。

整理:

RDEのrequired_actionは推奨アクションであり、最終決定はPolicy Bridgeが行うと明記するのがよい。

### 5.3 Creative Modeの制御

潜在的問題:

Creative Modeで許可範囲が広くなりすぎると、RDEが弱くなる。

修正提案:

Creative Modeでも、protected_elements、source_facts、citation integrity、user intent boundariesを必須にする。

### 5.4 Semantic Deltaの評価根拠

潜在的問題:

SemanticDeltaEngineがLLM evaluatorに依存しすぎる危険がある。

修正提案:

LLM evaluatorは一要素に限定し、domain-specific validators、tests、schema、AST、reference checkerを優先する設計原則を明記する。

## 6. 未解決問題

### 6.1 context_affinity更新

context_affinityはRDEにとって重要だが、更新規則は未確定である。Phase 2では保守的な近似でよいが、Phase 3ではmax/mean hybridまたは確率的定義が必要になる。

### 6.2 value alignment proxy

trust、stability、context_affinityでは、価値整合性を完全には表現できない。Institution Layerまたは明示的なvalue profileとの接続が必要である。

### 6.3 Semantic Diffの検証

意味差分の完全検出は不可能である。RDEは完全性ではなく、検出可能性、監査可能性、レビュー誘導を目標とすべきである。

### 6.4 Calibration data

trust/stability更新係数、risk threshold、classification thresholdにはログデータによる調整が必要である。

### 6.5 Human review boundary

どのリスクレベルで人間レビューを必須にするかは、個人利用、研究利用、企業利用、規制領域で異なる。Policy Profile化が必要である。

## 7. 実装順序の妥当性

推奨順序は妥当である。

```text
1. TaskContract schema
2. GeneratorOutput schema
3. StructuralDiff for Markdown/JSON/Python
4. RDEResult minimal classifier
5. AuditLog
6. PolicyBridge
7. SemanticDeltaEngine
8. RelationStore feedback
9. Tool execution gate
10. Institution Layer
```

理由:

- 早期に検証可能なMVPを作れる
- Structural Diffから始めるため、LLM evaluatorへの過依存を避けられる
- RelationStore feedbackは後段に置くため、初期実装の複雑性を抑えられる
- Institution Layerは現段階では未確定であり、後段に置くのが自然である

## 8. 総合判定

総合判定: 合格。Phase 1設計へ進める。

今回作成した2文書は、ここまでの議論を概ね正しく反映している。

特に次の点が強い。

1. RDEをOpenAyaneから抽出し、再度Ayaneへ戻す流れが明確である。
2. RDEをDiff、Policy、LLM Evaluatorから区別している。
3. Structural Diffを検出可能性の足場として位置づけている。
4. Generatorプロンプトを信頼ではなく監査可能性のために使っている。
5. 創造的逸脱と意味腐食を区別している。
6. 実装フェーズが現実的である。

ただし、次の点は次版で強化すべきである。

1. RDEとResonance Gateの境界をより明確にする。
2. Creative Modeでも保護対象を明示する。
3. SemanticDeltaEngineの非LLM検査優先順位を明記する。
4. context_affinityとvalue alignmentの未解決性を設計思想文書にも反映する。
5. RDEのrequired_actionをPolicyへのrecommendationとして明確化する。

## 9. 次の作業

次に行うべき作業は、Phase 1 MVP仕様への落とし込みである。

成果物候補:

```text
- RDE Core API Specification
- TaskContract JSON Schema
- StructuralDiff Plugin Specification
- MarkdownDiff MVP
- JsonSchemaDiff MVP
- PythonAstDiff MVP
- RDE Classification Test Corpus
- Generator System Prompt Pack
```

最初に作るべき最小セットは次である。

```text
TaskContract
GeneratorOutput
StructuralDiff
RDEResult
AuditEvent
```

この5つが揃えば、RDEは概念から実装へ移行できる。
