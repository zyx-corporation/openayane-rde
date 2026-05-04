---
title: "OpenAyane / RDE 設計思想ドキュメント"
version: "0.1-draft"
date: "2026-05-04"
author: "Tomoyuki Kano"
status: "conceptual draft"
---

# OpenAyane / RDE 設計思想ドキュメント

## 0. この文書の位置づけ

本書は、OpenAyane の設計経験から抽出された RDE（Resonant Deviation Evaluator）の概念を、独立した設計思想として定義し直すための文書である。

ここでの目的は、RDEを単なる validator、diff checker、policy filter、LLM evaluator に縮減しないことである。RDEは、生成系またはエージェント系が行う変換において、意味変化が許可された創造的逸脱なのか、静かに進行する意味腐食なのかを判定する評価構造である。

OpenAyane は、関係を時間積分された意味変化として扱い、relation_store、trust、stability、context_affinity、Structor、Policy、Audit によって、エージェントの実行を関係状態に条件づける構造として構想されてきた。RDEは、その設計経験を「意味逸脱の評価構造」として抽象化したものである。

```text
OpenAyane の設計経験
  ↓
関係・意味変化・構造評価・制度的制約の抽象化
  ↓
RDE 概念の確立
  ↓
Ayane / OpenAyane 実装への再導入
```

## 1. 背景: 生成系は保存ではなく再構成する

LLM（Large Language Model、大規模言語モデル）は、文書やコードを内部的に完全な構造物として保持し、その上で局所操作を行う機械ではない。実際には、入力、指示、文脈、履歴、ツール結果に条件づけられた再生成器として動作する。

そのため、LLMに「一部だけ直して」と依頼しても、出力は実質的には再構成された文書である。表面上は自然で、論理的に見え、タスクに従っているように見えても、数値、定義、制約、参照、論旨、依存関係が静かに変化することがある。

この現象を、本書では Silent ΔM と呼ぶ。

Silent ΔM は、明確な失敗ではない。むしろ、成功に見える出力の中で発生する。これが危険である。なぜなら、人間のレビューは「壊れていそうなもの」を探すが、Silent ΔM は「それらしく整ったもの」の中に潜むからである。

## 2. 中心問題: 意味同一性の保存は自動では成立しない

文書、コード、設定、会話、制度的判断には、保存されるべき同一性が存在する。

しかし、生成系における同一性は自動では保存されない。Git の差分、AST（Abstract Syntax Tree、抽象構文木）、JSON schema、DB schema、テスト、型検査のような外部構造がなければ、生成器は「何が変わってよく、何が変わってはいけないか」を安定して維持できない。

したがって、問題は単なる出力品質ではない。問題は、変換前後の意味状態を比較し、許可された変化と意図しない逸脱を分離する評価構造が欠けていることである。

## 3. RDEの定義

RDE（Resonant Deviation Evaluator）とは、生成系またはエージェント系が行う変換において、期待された意味変化と実際の意味変化との差分 ΔM を抽出し、その差分がタスク契約、文脈、関係履歴、制度的制約、リスク条件と共鳴しているかを評価する構造である。

短く定義すると、次のようになる。

> RDEは、生成系が生む意味逸脱を、許可された変化と危険な腐食に分離する評価構造である。

ここで重要なのは、RDEが変化そのものを禁止しない点である。RDEの対象は「変化があるか」ではなく、「その変化はどのような性質を持ち、どの許可構造に属しているか」である。

## 4. RDEが扱う三つの差分

RDEは、直接すべての意味を評価するのではなく、差分を複数層に分けて扱う。

### 4.1 Surface Diff

文字列、行、段落、トークン単位の差分である。通常の diff が扱う層であり、検出は容易だが意味解釈は弱い。

### 4.2 Structural Diff

文書やコードの構造差分である。JSONのキー、型、必須項目、PythonのAST、関数シグネチャ、Markdownの見出し階層、引用、定義、DB schema、依存関係、テスト対象などを比較する。

Structural Diff の目的は、意味逸脱をただちに判定することではない。目的は、意味差分を検出可能な形に落とすことである。

> Structural Diff は、LLMの「それっぽい再生成」を、検査可能な制度的対象へ引き戻す構造化レンズである。

### 4.3 Semantic Diff / ΔM

論旨、主張、制約、数値意味、定義、参照関係、安全条件、価値判断などの意味差分である。Structural Diff が検出した構造変化を足場にしつつ、意味的な保存・逸脱・破損を推定する。

## 5. 形式モデル

文書または状態を \(D_t\)、意味写像を \(M(D_t)\)、許可された変換を \(A_t\)、実際のLLM変換を \(\hat{A}_t\) とする。

期待される意味状態は次のように表せる。

\[
M_t^* = M(A_t(D_{t-1}))
\]

実際の意味状態は次のように表せる。

\[
\hat{M}_t = M(\hat{A}_t(D_{t-1}))
\]

意味逸脱は次のように定義する。

\[
\Delta M_t = \hat{M}_t - M_t^*
\]

RDEの仕事は、単に \(\Delta M_t\) の大きさを測ることではない。\(\Delta M_t\) が、許可された変換範囲、文脈、関係履歴、制度的制約に対して共鳴しているかを判定することである。

## 6. 逸脱分類

RDEは変化を一律に失敗と見なさない。最低限、次の分類を持つ。

### 6.1 Preserved

保存されるべき意味が保存されている状態。表層差分があっても、意味・構造・制約が維持されていれば Preserved となる。

### 6.2 Authorized Deviation

意味変化は存在するが、Task Contract によって明示的に許可されている状態。編集、要約、翻訳、リファクタリング、設計変更、仮説生成などがここに入る。

### 6.3 Benign Incidental Drift

要求範囲外の軽微な変化はあるが、リスクが低く、主張・制約・参照・実行結果に実質的影響を与えない状態。ただし、契約書、仕様書、医療、法務、金融、研究論文では、この分類の閾値は極めて低く設定されるべきである。

### 6.4 Suspicious Drift

指示外の意味変化があり、許可範囲との整合が曖昧な状態。自動承認してはならず、人間レビューまたは上位評価が必要である。

### 6.5 Critical Corruption

数値、定義、制約、参照、識別子、依存関係、安全条件、実行前提などが意図せず破壊されている状態。原則として停止、差し戻し、ロールバック、または高優先度レビューが必要である。

### 6.6 Creative Deviation

既存構造から意図的に逸脱し、新しい構造、仮説、表現、設計を生成する状態。これは悪ではない。ただし、創造的逸脱は必ず署名可能でなければならない。

```text
良い創造的逸脱:
  どこを壊したかが明示される
  なぜ壊したかが説明される
  何を保存したかが列挙される
  元に戻せる
  検証可能である

悪い逸脱:
  変化が沈黙している
  保存対象が壊れている
  Generator自身も変化を認識していない
  検証不能である
```

## 7. Task Contract

RDEの精度は、許可された変換がどれだけ明示化されているかに大きく依存する。したがって、Generatorに直接曖昧な指示を渡すのではなく、Task Contract を作る。

Task Contract は次の要素を持つ。

```yaml
TaskContract:
  requested_action: "文体をですます調に統一する"
  mode: "preservation"
  allowed_delta_m:
    - "語尾の統一"
    - "重複表現の削除"
    - "接続表現の調整"
  forbidden_delta_m:
    - "主張の変更"
    - "定義文の変更"
    - "数値の変更"
    - "引用の削除"
    - "見出し階層の変更"
  protected_elements:
    - "numbers"
    - "definitions"
    - "citations"
    - "references"
    - "constraints"
  review_policy:
    suspicious_drift: "human_review"
    critical_corruption: "halt"
```

Task Contract は、Generatorのためだけではなく、RDEのための評価基準でもある。

## 8. Generatorへの要求

Generatorには、Structural Diff と RDE が働きやすい出力を生成させるべきである。ただし、その目的は Generator を信頼することではない。Generatorを監査可能にすることである。

Generatorは次を出力する。

```yaml
GeneratorOutput:
  result: "変換後本文またはpatch"
  self_report:
    changed_elements: []
    unchanged_elements: []
    deleted_elements: []
    added_elements: []
    semantic_risk_notes: []
    uncertainty_notes: []
```

Generatorの自己申告は真とは見なさない。むしろ、自己申告とStructural Diffの不一致こそが重要なシグナルである。

```text
実際の差分 - 自己申告差分 = 認識されていない逸脱
```

## 9. RDEとOpenAyaneの対応関係

RDEはOpenAyaneから独立して定義できるが、OpenAyaneの各要素と自然に対応する。

| OpenAyaneでの概念 | RDEでの抽象化 |
|---|---|
| relation_store | 意味変化の履歴基盤 |
| ΔM update | 逸脱量・方向・履歴の評価 |
| trust | 変換主体・出力・経路への信頼重み |
| stability | 変化パターンの安定性 |
| context_affinity | 現在の変換が関係文脈に属するか |
| Structor | 生成された思考・計画・構造の事前評価 |
| Policy | 許可・停止・レビュー・ロールバックの規則 |
| resonance gate | 逸脱が共鳴しているかの実行判定 |
| Audit | 変化の署名と責任追跡 |

この対応により、RDEはOpenAyaneの中に戻せる。

```text
Generator / Agent Action
  ↓
Output or Patch
  ↓
Structural Diff
  ↓
Semantic ΔM Estimator
  ↓
RDE
  ↓
Policy / Approval / Rollback
  ↓
RelationStore Update
```

## 10. RDEとPolicyの違い

Policyは規則を扱う。RDEは意味変化を扱う。

Policyの問いは次である。

```text
これは許可されているか。
```

RDEの問いは次である。

```text
これは何をどのように変えたか。
その変化は許可されたΔMか。
それともSilent ΔMか。
```

RDEはPolicyの下位部品ではない。Policyが扱える形に意味変化を変換する評価層である。

## 11. RDEとDiffの違い

Diffは差分を出す。RDEは差分の意味と許可性を裁定する。

Structural Diff はRDEに必要な入力であるが、RDEそのものではない。Structural Diff が「構造が変わった」と示し、Semantic Diff が「意味が変わった可能性」を示し、RDEが「それは許可された変化か」を判定する。

## 12. RDEとLLM Evaluatorの違い

RDEはLLMではない。LLM evaluatorを使うことはできるが、RDEそのものは評価アーキテクチャである。

RDEは以下を組み合わせる。

```text
- ルールベース検査
- schema検査
- AST検査
- テスト結果
- 型検査
- 参照整合性検査
- LLMによる意味評価
- relation_store履歴
- policy制約
- audit log
```

この多層性が、単一LLM evaluatorへの依存を避ける。

## 13. モード設計

RDEはタスクモードごとに許可するΔMを変える。

### 13.1 Preservation Mode

仕様書、契約、コード、研究論文校正などに用いる。保存対象を最大化する。

### 13.2 Creative Mode

構想、エッセイ、コピー、仮説生成などに用いる。逸脱を許容するが、逸脱の自己署名とRDE分類を必須にする。

### 13.3 Refactor Mode

コードや設計の構造変更に用いる。内部構造の変更は許可するが、外部仕様、テスト契約、API契約、意味契約は保持する。

### 13.4 Research Mode

仮説生成、論点拡張、反例探索に用いる。既存事実、引用、根拠、仮説、推測を明確に分離する。

## 14. 設計原則

### 原則1: 生成と評価を分離する

Generatorは変換案を生成する。RDEは変換の意味的副作用を評価する。Generator自身に最終評価を任せない。

### 原則2: 変化を禁止せず、分類する

すべての変化を誤りと見なすと、創造性が死ぬ。RDEは変化を保存、許可、疑義、破壊、創造的逸脱に分類する。

### 原則3: 意味変化を履歴化する

単発の逸脱だけでなく、同じAgent、同じ文書、同じ関係、同じドメインで繰り返されるΔMパターンを記録する。

### 原則4: 評価は制度的に署名可能であるべき

誰が、何を、なぜ変え、どの制約に照らして承認されたかを追跡できるようにする。

### 原則5: 完全保存ではなく、評価可能性を目標とする

意味の完全同一性は多くのドメインで不可能である。重要なのは、差異を観測可能、制約可能、更新可能にすることである。

## 15. 研究仮説

RDEを研究対象として立てる場合、次の仮説が中心になる。

1. LLMの長期委任劣化は単純な誤差蓄積ではなく、意味再生成に伴うΔMジャンプ過程である。
2. 創造的編集と文書破損の差は、ΔMの大きさではなく、ΔMの許可性、可逆性、検証可能性、制度的署名性によって決まる。
3. モデル性能向上だけではSilent ΔMを消せない。必要なのは、GeneratorとEvaluatorの分離、Structural Diff、Semantic Diff、履歴管理、RDEによる共鳴逸脱判定を含むアーキテクチャである。
4. RDEをRelationStoreへ接続することで、単発評価を超えて、Agentの長期信頼性と文脈適合性を更新できる。

## 16. Ayaneへの再導入方針

RDEは、OpenAyaneに次の形で再導入する。

```text
Task Contract Builder
  ↓
Generator Adapter
  ↓
Structural Diff Engine
  ↓
Semantic Delta Engine
  ↓
RDE Core
  ↓
Policy Bridge
  ↓
RelationStore / AuditLog / Rollback
```

最初の対象ドメインは、Markdown、JSON、Pythonに限定する。これにより、Structural Diff を比較的安定して実装できる。

## 17. 非目標

RDEは以下を目標にしない。

- すべての意味変化を完全に検出すること
- すべてのLLM出力を自動承認可能にすること
- PolicyやInstitution Layerを置き換えること
- LLM evaluatorだけで意味を裁定すること
- 創造的逸脱を抑圧すること

## 18. 結論

RDEは、OpenAyaneの設計経験から抽出された「意味変化の監査構造」である。

それは、生成系が残す足跡を読み、それが創造の歩みなのか、意味腐食の痕跡なのかを判定する。

OpenAyaneは、RDEを実装する最初の制度的アーキテクチャである。そしてRDEは、OpenAyaneを単なるエージェント安全機構から、意味変化を扱う一般的な知性基盤へ押し上げる中核概念である。
