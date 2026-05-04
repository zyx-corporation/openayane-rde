# OpenAyaneの実装計画：RDE評価器に基づく意味変化監査機構の設計と段階的実装

## 要旨

本稿は、OpenAyaneを、生成AIおよびエージェント型AIの出力・編集・実行過程における意味変化を監査する実装可能な機構として定式化し、その段階的実装計画を研究論文形式で提示する。大規模言語モデルは、文書・コード・計画を厳密に保存しながら局所変更する機械ではなく、入力、履歴、指示、文脈に基づいて対象を再生成するシステムである。そのため、表面的には自然で有用に見える出力の内部で、定義、制約、数値、参照、論旨、依存関係が静かに変化することがある。本稿では、この現象を Silent ΔM と呼び、単なる誤生成ではなく、生成系に固有の意味再構成過程として扱う。

OpenAyaneは、このSilent ΔMに対して、RDE（Resonant Deviation Evaluator）を中核評価器として導入する。RDEは、通常のDiff、Policy Filter、Validator、LLM Evaluatorそのものではない。RDEは、変換前状態、期待された変換、実際の生成結果の差異を、タスク契約、文脈、関係履歴、制度的制約と照合し、その意味変化が保存、許可された逸脱、軽微な副次的変化、疑義ある逸脱、重大な腐食、創造的逸脱のいずれに属するかを分類する評価構造である。

一方、OpenAyaneはRDEそのものではない。OpenAyaneは、RDEを含み、Task Contract生成、Generator制御、Structural Diff、Semantic Delta、Policy Bridge、Safe Execution Runtime、AuditLog、RelationStore更新、履歴参照ループを統合する関係的制御機構である。したがって、RDEの問いは「この意味変化は何か」であり、OpenAyaneの問いは「その評価結果を、どの制度的・関係的制御ループの中で、どのように扱うか」である。

本稿の貢献は三点である。第一に、生成AI委任における文書・コード破壊を、単なる品質問題ではなく意味変化監査問題として再定義する。第二に、OpenAyaneの実装計画を、Task Contract、Generator Adapter、Structural Diff Engine、Semantic Delta Engine、RDE Core、Policy Bridge、Relation Store、Audit Engineからなる段階的機構として示す。第三に、Phase 1 MVPからInstitution Layer接続までの実装・評価・受け入れ基準を提示し、RDEを理論概念から実装可能な評価器へ、OpenAyaneをその評価器を作動させる実行・監査機構へ移行させる。

キーワード：OpenAyane、RDE、Resonant Deviation Evaluator、Silent ΔM、意味変化、エージェント安全性、Structural Diff、Semantic Diff、Relation Store、AIガバナンス

## 1. はじめに

生成AIの実用化は、文章生成、要約、翻訳、コード補完、設計支援、業務自動化を急速に進展させた。しかし、その進展とともに、生成AIへの長期委任に固有の失敗も明らかになりつつある。典型的には、ユーザーが「この一部だけ修正して」「文体だけ整えて」「アルゴリズムは変えずにエラー処理を追加して」と依頼したにもかかわらず、生成結果において主張、定義、数値、引用、依存関係、API、テスト条件などが静かに変化する。

この問題は、従来の意味でのハルシネーションだけでは説明できない。なぜなら、多くの場合、出力は滑らかで、形式的には整い、ユーザーの要求に従っているように見えるからである。問題は、生成AIが対象を「保存された構造物」として扱うのではなく、「文脈に応じて再構成される状態」として扱う点にある。したがって、生成AIにおける危険は、明白に壊れた出力よりも、成功に見える出力の内部に潜む未署名の意味変化にある。

本稿では、この未署名の意味変化を Silent ΔM と呼ぶ。ΔMは意味状態の変化であり、Silent ΔMはユーザー、システム、または生成器自身によって十分に明示・署名・監査されない意味変化である。Silent ΔMは、文章編集、研究論文校正、仕様書更新、コードリファクタリング、エージェント実行計画、外部ツール呼び出しのいずれにおいても生じうる。

本稿の目的は、OpenAyaneの実装計画を、Silent ΔMへの対処を中核とする研究論文として整理することである。OpenAyaneは、単なるエージェント実行基盤ではない。OpenAyaneは、生成系が行う変換を、関係状態、意味変化、制度的制約、監査可能性に基づいて制御する機構である。その中核評価器に置かれるのが、RDEである。

RDEは、生成結果が良いか悪いかを単純に評価する仕組みではない。また、Diffを出すだけのツールでもない。RDEの問いは、「何が変わったか」「その変化は許可されていたか」「その変化は元の意図・価値・設計思想と共鳴しているか」「その変化は創造的逸脱なのか、意味腐食なのか」である。

一方で、OpenAyaneの問いはさらに広い。OpenAyaneは、RDEの評価結果を受け取り、承認、差し戻し、停止、ロールバック、AuditLog記録、RelationStore更新、次回判断条件の変更へ接続する。したがって、OpenAyaneは単発の評価器ではなく、過去のΔMを読み、現在の変換を評価し、未来の許可条件を更新する関係的制御機構である。

## 2. 背景と問題設定

### 2.1 生成AIは保存ではなく再構成する

従来の編集システムでは、対象文書やコードは明示的な構造物として保存され、変更操作はその構造物の一部に対して行われる。GitのDiff、AST（Abstract Syntax Tree、抽象構文木）、型システム、テスト、スキーマ、DB制約などは、こうした局所変更を外部的に検査するための制度的装置である。

しかし、大規模言語モデルは、内部的に対象文書を完全な操作対象として保持し、その一部だけを機械的に変更するわけではない。LLM（Large Language Model、大規模言語モデル）は、入力、指示、コンテキスト、過去履歴、推論過程に基づいて、もっともらしい出力を再生成する。したがって、ユーザーが局所変更を求めても、出力全体は再構成された生成物である。

この再構成性は、生成AIの能力の源泉でもある。単なる文字列置換ではなく、文脈を踏まえた言い換え、補完、構成変更、抽象化、創造的提案が可能になるからである。しかし同時に、再構成性は保存対象を破壊する危険を持つ。生成AIは、どの意味を保存し、どの意味を変化させてよいかを、外部構造なしに安定して保持できない。

### 2.2 Silent ΔMの危険性

Silent ΔMの危険は、それが明白な失敗として現れない点にある。数値がわずかに変わる。定義が弱くなる。引用が一般化される。条件節が削られる。コードの関数シグネチャが微妙に変化する。テストが通るように見えるが、元の仕様を保証しなくなる。これらは、表面上は読みやすさや整合性の改善として現れることさえある。

特に危険なのは、以下の領域である。

- 研究論文：定義、仮説、引用、限界、主張の強度が変化する。
- 仕様書：必須条件、禁止条件、責任境界、例外条件が変化する。
- コード：API、例外処理、セキュリティ条件、テスト前提が変化する。
- 法務・契約：義務、免責、責任、期間、対象範囲が変化する。
- エージェント実行：計画意図、権限、対象、外部副作用が変化する。

この問題は、モデル性能の向上だけでは解消されない。性能が高いモデルほど、壊れた出力を自然に整える能力も高くなるため、むしろSilent ΔMは検出しにくくなる可能性がある。必要なのは、生成器の賢さに依存することではなく、生成器の変換を監査可能にする外部構造である。

### 2.3 変化は悪ではない

重要なのは、変化そのものを悪と見なさないことである。編集、要約、翻訳、リファクタリング、研究、設計、創造的執筆はいずれも意味変化を伴う。意味変化をすべて禁止すれば、生成AIの価値は失われる。

したがって問題は、「変化があるか」ではない。問題は、「その変化が許可された変化なのか」「その変化が署名可能なのか」「その変化が元の意図と整合しているのか」「その変化が検証可能で可逆なのか」である。OpenAyaneは、この問いに対してRDEを導入する。

### 2.4 単発評価から履歴参照ループへ

Silent ΔMへの対処は、単発の評価だけでは不十分である。一回ごとの変更が軽微でも、同じ生成器が繰り返し引用を弱める、数値を丸める、制約条件を省略する、定義を一般化する傾向を持つ場合、その危険は連鎖的に蓄積する。

そのため、OpenAyaneは単発のRDE判定だけでなく、AuditLogとRelationStoreによって過去の変化を保存し、次回以降の判断条件へ戻す必要がある。AuditLogは過去に何が起きたかの不可逆的記録であり、RelationStoreはその履歴から抽出された関係状態である。

この履歴参照ループにより、OpenAyaneは「今回の出力を評価する機構」から、「過去のΔMを読み、現在の変換を評価し、未来の許可条件を更新する機構」へ拡張される。

## 3. RDEの概念定義

RDE（Resonant Deviation Evaluator）とは、生成系またはエージェント系が行う変換において、期待された意味変化と実際の意味変化との差分ΔMを抽出し、その差分がタスク契約、文脈、関係履歴、制度的制約、リスク条件と共鳴しているかを評価する構造である。

RDEの簡潔な定義は次のとおりである。

> RDEは、生成系が生む意味逸脱を、許可された変化と危険な腐食に分離する評価構造である。

RDEは、通常のValidatorではない。Validatorは規則への適合を検査する。RDEは、意味変化の性質と許可性を評価する。RDEは、Diff Checkerではない。Diff Checkerは差分を抽出する。RDEは、差分が何を意味するかを裁定する。RDEは、Policy Filterでもない。Policy Filterは許可・禁止の規則を扱う。RDEは、Policyが判断可能な形に意味変化を変換する。RDEは、LLM Evaluatorそのものでもない。LLM Evaluatorを部品として用いることはできるが、RDEはルール、スキーマ、AST、テスト、型検査、参照検査、履歴、Policy、Auditを組み合わせる評価アーキテクチャである。

## 4. RDEとOpenAyaneの役割分担

本稿では、RDEとOpenAyaneを明確に区別する。RDEは評価器であり、OpenAyaneは機構である。

RDEは、生成系またはエージェント系が生む意味変化ΔMを評価し、その変化が保存、許可された逸脱、軽微な副次的変化、疑義ある逸脱、重大な腐食、創造的逸脱のいずれに属するかを分類する評価器である。

一方、OpenAyaneはRDEそのものではない。OpenAyaneは、RDEを中核評価器として組み込み、Task Contract生成、Generator制御、Structural Diff、Semantic Delta、Policy Bridge、Safe Execution Runtime、AuditLog、RelationStore更新、履歴参照ループを統合する実行・監査機構である。

したがって、RDEの問いは次である。

```text
この意味変化は何か。
その変化は許可されたΔMか。
それともSilent ΔMか。
それは創造的逸脱か、意味腐食か。
```

OpenAyaneの問いは次である。

```text
その評価結果をどのように扱うか。
承認するのか、差し戻すのか、停止するのか。
ロールバックするのか、AuditLogにどう記録するのか。
RelationStoreをどう更新し、次回判断条件へどう戻すのか。
```

この区別により、RDEはOpenAyane以外にも応用可能な評価器として抽象化される。一方、OpenAyaneは、RDE評価結果を実行制御、監査、履歴更新、制度的責任へ接続する機構として位置づけられる。

## 5. 形式モデル

文書または状態を \(D_t\)、意味写像を \(M(D_t)\)、許可された変換を \(A_t\)、実際の生成器による変換を \(\hat{A}_t\) とする。

期待される意味状態は次のように表される。

\[
M_t^* = M(A_t(D_{t-1}))
\]

実際の意味状態は次のように表される。

\[
\hat{M}_t = M(\hat{A}_t(D_{t-1}))
\]

意味逸脱は次のように定義される。

\[
\Delta M_t = \hat{M}_t - M_t^*
\]

ただし、RDEの目的は単に \(\|\Delta M_t\|\) を最小化することではない。創造的変換や設計変更では、大きなΔMが正当な場合がある。RDEの目的は、ΔMの大きさ、方向、対象、許可性、可逆性、検証可能性、制度的署名性を評価することである。

そのため、RDEは以下の関数として抽象化できる。

\[
RDE(\Delta M_t, C_t, R_t, P_t, I_t) \rightarrow (class, risk, recommendation, explanation)
\]

ここで、\(C_t\)はTask Contract、\(R_t\)はRelation State、\(P_t\)はPolicy、\(I_t\)はInstitutional Constraintである。出力は、逸脱分類、リスク水準、推奨アクション、説明からなる。

重要なのは、ここで返される recommendation はOpenAyaneの最終実行判断そのものではない点である。RDEは評価器であり、最終的な承認、差し戻し、停止、ロールバックはOpenAyane側のPolicy BridgeとModification Control Flowが担う。

## 6. OpenAyaneアーキテクチャ

OpenAyaneは、RDEを中核評価器として、生成、差分抽出、意味評価、Policy判断、実行制御、関係更新、監査、履歴参照を接続する。

実装上の主要フローは次の通りである。

```text
User / External Trigger
  ↓
Intent Parser
  ↓
RelationContext Loader
  ↓
Task Contract Builder
  ↓
Generator Adapter
  ↓
Generated Output or Patch
  ↓
Structural Diff Engine
  ↓
Semantic Delta Engine
  ↓
RDE Core
  ↓
Policy Bridge
  ↓
Modification Control Flow
  ↓
Safe Execution Runtime / File Patch / Tool Call
  ↓
AuditLog
  ↓
RelationStore Update
  ↓
Historical Context Feedback
  ↺ back to RelationContext Loader / Task Contract Builder / RDE Core / Policy Bridge
```

この構成により、OpenAyaneは出力単体を評価するのではなく、変換前状態、許可された変換、生成後状態の三者関係を評価し、さらにその評価結果を次回以降の判断条件へ戻す。

### 6.1 Forward Evaluation Loop

Forward Evaluation Loopは、ユーザー要求または外部イベントから、生成、差分評価、RDE判定、Policy判断、実行制御までの前向きの流れである。

```text
User / External Trigger
  ↓
Intent Parser
  ↓
RelationContext Loader
  ↓
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
Execution / Apply / Reject
  ↓
AuditLog + RelationStore Update
```

この前向きループは、従来のAgent実行パイプラインに近い。しかしOpenAyaneでは、生成器の出力をそのまま実行せず、Task Contract、Structural Diff、Semantic Delta、RDE Core、Policy Bridgeを通す点が異なる。

### 6.2 Historical Feedback Loop

Historical Feedback Loopは、AuditLogとRelationStoreから次回判断へ戻る履歴参照ループである。

```text
AuditLog
  ↓
Past task contracts
Past diffs
Past RDE classifications
Past policy decisions
Past rollbacks
Human review outcomes
  ↓
RelationStore
  ↓
trust
stability
context_affinity
drift patterns
domain risk profile
generator reliability profile
document fragility profile
  ↓
RelationContext Loader
  ↓
Task Contract Builder / RDE Core / Policy Bridge
```

ここで重要なのは、AuditLogとRelationStoreの役割を分離することである。AuditLogは、過去に何が起きたかの不可逆的な記録である。RelationStoreは、その履歴から抽出された関係状態である。

したがって、同じGeneratorが繰り返し「引用を弱める」「数値を丸める」「制約条件を省略する」傾向を持つなら、一回ごとの変更は軽微でも、RelationStore上ではdrift patternとして蓄積される。次回以降、そのGeneratorに対するtrustを下げ、同じ文脈でのreview thresholdを上げることができる。

この履歴参照ループこそが、OpenAyaneを単なるRDE実装から、関係ベースの意味変化監査機構にしている部分である。

## 7. OpenAyane主要モジュール

### 7.1 Intent Parser

Intent Parserは、ユーザー要求、システムイベント、エージェント内部計画を解析し、操作意図を抽出する。例えば、文書編集、コード変更、ツール実行、要約、リファクタリング、調査などである。

重要なのは、Intent Parserが曖昧な自然言語指示を、そのままGeneratorへ渡さないことである。自然言語指示は、次段のTask Contract Builderによって評価可能な契約へ変換される。

### 7.2 RelationContext Loader

RelationContext Loaderは、現在のタスクに関連する履歴状態をRelationStoreから読み込む。対象となる履歴は、生成主体、対象文書、作業空間、ツール、ユーザー、ドメイン、過去の失敗パターンなどである。

このモジュールは、OpenAyaneを単発評価から履歴参照型制御へ変えるための接続点である。例えば、ある文書が過去に数値のSilent ΔMを頻繁に起こしている場合、同じ文書に対する次回編集では、Task Contract Builderがnumbersをprotected_elementsに入れ、RDE Coreが数値変更に対するriskを高く評価する。

### 7.3 Task Contract Builder

Task Contractは、RDEの評価基準である。生成器に「何をしてよいか」を伝えるだけでなく、RDEに「何が許可されたΔMか」を与える。

Task Contractは、少なくとも以下の要素を持つ。

```yaml
TaskContract:
  contract_id: "uuid"
  mode: "preservation | creative | refactor | research | execution"
  target_scope:
    files: []
    symbols: []
    sections: []
  requested_action: "要求された変換"
  allowed_delta_m: []
  forbidden_delta_m: []
  protected_elements: []
  output_policy:
    require_patch: true
    require_change_report: true
    require_uncertainty_report: true
  review_policy:
    preserved: "auto_approve"
    authorized_deviation: "auto_approve_or_note"
    benign_incidental_drift: "approve_with_note"
    suspicious_drift: "human_review"
    critical_corruption: "halt"
```

Task Contractの導入により、OpenAyaneは「曖昧な依頼に対して、曖昧な生成を返す」構造から、「許可された変換に対して、監査可能な生成を返す」構造へ移行する。

### 7.4 Generator Adapter

Generator Adapterは、OpenAI、Claude、Gemini、Ollama、local model、specialized toolなどを抽象化する。OpenAyaneにおいて、Generatorは最終判断者ではない。Generatorは変換候補を生成する主体であり、その出力はStructural Diff、Semantic Delta、RDEによって検査される。

Generatorには、Task Contractに基づき、本文またはpatchに加えて、構造化されたself_reportを出力させる。

```yaml
GeneratorOutput:
  output_type: "full_text | patch | plan | tool_call"
  payload: "本文またはpatch"
  self_report:
    changed_elements: []
    unchanged_elements: []
    added_elements: []
    deleted_elements: []
    semantic_risk_notes: []
    uncertainty_notes: []
```

ただし、このself_reportは信頼されない。むしろ、Generatorの自己申告と実際のStructural Diffの差分こそが重要なリスク信号である。

```text
実際の差分 - 自己申告差分 = 認識されていない逸脱
```

### 7.5 Structural Diff Engine

Structural Diff Engineは、対象ドメインごとの構造差分を抽出する。Markdownであれば見出し階層、定義、引用、リンク、表、コードブロックを扱う。JSONであればキー、型、必須項目、スキーマ制約、配列長を扱う。PythonであればAST、import、関数シグネチャ、class定義、制御フロー、例外処理、テストを扱う。

Structural Diffは、意味判定そのものではない。Structural Diffは、意味判定のための構造化レンズである。LLMの再生成結果を、検査可能な制度的対象へ引き戻す役割を持つ。

### 7.6 Semantic Delta Engine

Semantic Delta Engineは、Structural Diffを足場に、意味差分を推定する。対象は、主張、定義、制約、数値、引用、参照、安全条件、仕様、テスト前提などである。

Semantic Delta Engineは、LLM evaluatorに過度に依存してはならない。優先されるべきは、スキーマ検査、AST検査、型検査、テスト、参照整合性検査、domain-specific validatorである。LLM evaluatorは、これらで捕捉しにくい意味変化の候補抽出や説明生成に用いられるべきである。

### 7.7 RDE Core

RDE Coreは、Semantic DeltaをTask Contract、Policy、Relation Stateと照合し、逸脱分類と推奨アクションを出す。

```yaml
RDEResult:
  classification: "preserved | authorized_deviation | benign_incidental_drift | suspicious_drift | critical_corruption | creative_deviation"
  resonance_score: 0.0
  preservation_score: 0.0
  risk_level: "low | medium | high | critical"
  violated_constraints: []
  suspicious_elements: []
  required_action: "approve | approve_with_notes | request_revision | human_review | halt | rollback"
  explanation: "判定理由"
```

ここで注意すべきは、RDEのrequired_actionは最終決定ではなく、Policy Bridgeへの推奨であるという点である。最終的な承認、差し戻し、停止、ロールバックはPolicy Bridgeが行う。

### 7.8 Policy Bridge

Policy Bridgeは、RDEの判定を実行制御へ変換する。Policyは規則を扱い、RDEは意味変化を扱う。したがって、RDEはPolicyの下位部品ではなく、Policyが判断可能な証拠を生成する中間評価層である。

例えば、Preservedであれば承認、Authorized Deviationであれば承認または注記付き承認、Suspicious Driftであれば人間レビュー、Critical Corruptionであれば停止またはロールバックといった対応が考えられる。

### 7.9 Modification Control Flow

Modification Control Flowは、変更提案、RDE評価、承認、適用、ロールバックを管理する。これは、RDE評価結果を実際の状態変更に接続する制御層である。

```text
propose_change
  ↓
run_diff
  ↓
run_rde
  ↓
decide
  ↓
apply_or_reject
  ↓
audit
```

ここで重要なのは、RDEが評価器である以上、実際に変更を適用する責任はModification Control Flowにあるという点である。RDEは「危険である」「許可されている」「レビューが必要である」と評価するが、実行そのものはOpenAyane機構側が担う。

### 7.10 Safe Execution Runtime

Safe Execution Runtimeは、外部ツール、ファイルシステム、ネットワーク、メール、カレンダー、決済などの実行をsandbox、権限、timeout、resource limitで制御する。

Phase 3以降では、文書編集やコード変更だけでなく、Agentのツール実行前にRDEとPolicy Bridgeを通す。これにより、Agentが外部副作用を伴う操作を行う前に、その操作がTask Contract、Relation State、context_affinity、Policyと整合しているかを評価できる。

### 7.11 AuditLog

AuditLogは、Task Contract、Generator Output、Structural Diff、Semantic Delta、RDE Result、Policy Decision、実行結果、ロールバック、人間レビューを記録する。OpenAyaneにおいて、監査性は付加機能ではなく中核要件である。

AuditLogは、過去に何が起きたかの不可逆的記録である。誰が、何を、なぜ変え、どの基準で承認されたかが追跡可能でなければ、意味変化は制度的に扱えない。

### 7.12 Relation Store

Relation Storeは、Agent、User、Tool、Document、Workspace間の関係状態を保存する。RDEの結果は、その場限りの判断ではなく、長期的なtrust、stability、context_affinityに反映される。

```yaml
RelationState:
  subject_id: "agent-or-user"
  object_id: "user-tool-document-workspace"
  trust: 0.0
  stability: 0.0
  context_affinity: 0.0
  interaction_count: 0
  last_delta_m: 0.0
  delta_m_history_summary: {}
  drift_patterns: []
  generator_reliability_profile: {}
  document_fragility_profile: {}
  last_updated_at: "timestamp"
```

この構造により、OpenAyaneは単発の出力評価を超え、生成主体・対象文書・作業文脈ごとの長期信頼性を更新できる。

## 8. RDE判定アルゴリズム

RDE判定の基本形は以下のように表現できる。

```python
def evaluate_rde(original, generated, contract, relation_state, policy):
    structural = structural_diff(original, generated, contract)
    semantic = semantic_delta(original, generated, contract, structural)

    preservation = score_preservation(semantic, contract.protected_elements)
    authorization = score_authorization(
        semantic,
        contract.allowed_delta_m,
        contract.forbidden_delta_m,
    )
    resonance = score_resonance(semantic, relation_state, contract)
    risk = score_risk(structural, semantic, contract)

    classification = classify(
        preservation=preservation,
        authorization=authorization,
        resonance=resonance,
        risk=risk,
        mode=contract.mode,
    )

    recommendation = policy_recommend(classification, risk, contract.review_policy)

    return RDEResult(
        classification=classification,
        resonance_score=resonance,
        preservation_score=preservation,
        risk_level=risk,
        required_action=recommendation,
    )
```

このアルゴリズムは、RDEの最小構成を示すものであり、Phase 1ではStructural Diffと簡易分類に限定してよい。Phase 2以降でSemantic DeltaとRelation Store更新を追加し、Phase 3でAgent Execution Gateへ拡張する。

### 8.1 OpenAyane側の制御アルゴリズム

RDEが評価器であるなら、OpenAyane側にはその評価結果を扱う制御アルゴリズムが必要である。

```python
def run_openayane_flow(trigger):
    intent = parse_intent(trigger)
    relation_context = load_relation_context(intent)
    contract = build_task_contract(intent, relation_context)

    generated = generator_adapter.generate(contract)
    rde_result = evaluate_rde(
        original=contract.original_state,
        generated=generated.payload,
        contract=contract,
        relation_state=relation_context,
        policy=load_policy(contract),
    )

    decision = policy_bridge_decide(rde_result, contract, relation_context)
    execution_result = modification_control(decision, generated, contract)

    audit_event = write_audit_log(
        contract=contract,
        generated=generated,
        rde_result=rde_result,
        decision=decision,
        execution_result=execution_result,
    )

    update_relation_store(audit_event, rde_result, execution_result)

    return execution_result
```

この擬似コードでは、RDEがOpenAyaneの内部に存在しつつ、OpenAyane全体とは同一ではないことが明確になる。RDEは評価を返す。OpenAyaneは、その評価を制度的・実行的・履歴的に処理する。

## 9. 実装フェーズ

### 9.1 Phase 0: Concept Freeze

Phase 0では、RDEの定義、Task Contractの構造、逸脱分類、OpenAyane既存モジュールとの対応関係を固定する。この段階では実装よりも、概念境界の確定が重要である。

特に以下を明確化する。

- RDEはDiffではない。
- RDEはPolicyではない。
- RDEはLLM Evaluatorではない。
- RDEは評価器であり、OpenAyaneは機構である。
- Structural DiffはRDEが働くための構造化レンズである。
- RDEのrequired_actionはPolicyへの推奨であり、最終決定ではない。
- Resonance GateはRDEそのものではなく、RDE結果とRelation Stateを使う実行判定機構である。
- AuditLogとRelationStoreは履歴参照ループの基盤である。

### 9.2 Phase 1: Structural RDE MVP

Phase 1では、対象をMarkdown、JSON、Pythonに限定し、Structural Diffを中心とするMVPを実装する。

最小構成は次の五つである。

```text
TaskContract
GeneratorOutput
StructuralDiff
RDEResult
AuditEvent
```

この段階の目標は、完全な意味理解ではない。許可外の構造変更を検出し、Generatorの自己申告と実Diffの不一致を記録し、高リスクな破壊を自動適用前に停止することである。

Phase 1の受け入れ基準は以下である。

1. Markdownで見出し、引用、定義、数値の許可外変更を検出できる。
2. JSONでschema key、type、required fieldの破壊を検出できる。
3. Pythonでfunction signature、import、主要AST変更を検出できる。
4. Generator self_reportと実diffの不一致を記録できる。
5. RDEResultがpreserved、authorized_deviation、suspicious_drift、critical_corruptionを返せる。
6. AuditLogにTaskContract、Diff、RDE、Policy decisionが保存される。
7. Critical Corruptionで自動適用が停止する。

### 9.3 Phase 2: Semantic ΔM + Relation Feedback

Phase 2では、Semantic Delta EngineとRelation Store更新を導入する。Phase 1で構造的に検出された差分をもとに、意味変化の疑義分類を行う。

この段階で導入する要素は以下である。

- Changed claims tracking
- Definition preservation check
- Numeric consistency check
- Reference integrity check
- Safety condition tracking
- Relation Store feedback
- trust / stability / context_affinity provisional update
- LLM evaluator ensemble

ただし、context_affinityの更新規則は未確定であり、Phase 2では保守的な近似でよい。Phase 3以降で、max/mean hybrid、分布的更新、異常文脈侵入への耐性を導入する。

### 9.4 Phase 3: Agent Execution Gate

Phase 3では、文書編集やコード変更だけでなく、エージェントのツール実行前にRDEを接続する。

この段階では、Structor、Policy Bridge、Safe Execution Runtime、Tool Call Gating、Rollback Managerを統合する。RDEは、実行前の計画がTask Contract、Relation State、context_affinity、Policyと整合しているかを評価し、外部副作用を伴う操作を制御する。

重要なのは、RDEがResonance Gateそのものではない点である。RDEは意味逸脱を評価し、Resonance Gateはその評価とRelation Stateを用いて実行可否を決める。

### 9.5 Phase 4: Institution Layer

Phase 4では、OpenAyaneを内部Policyに閉じず、外部制度的根拠へ接続する。候補としては、PoP-UID、DAOまたは組織Policy、外部監査、規範レジストリ、権限委任、本人性証明などがある。

この段階での目的は、RDEの判断を個別エージェントの内部閾値に閉じず、責任、権限、承認、制度的署名に接続することである。

## 10. 評価計画

OpenAyaneの評価は、単なる生成品質評価では不十分である。評価対象は、意味変化の検出、分類、承認制御、監査可能性、長期安定性である。

### 10.1 Unit Tests

Unit Testsでは、TaskContract生成、StructuralDiff検出、RDE分類、Policy決定、RelationStore更新を個別に検証する。

### 10.2 Golden Tests

Golden Testsでは、既知の入力、出力、期待分類を固定し、RDEが安定して同じ判断を返すかを確認する。RDEは確率的LLM evaluatorを含みうるため、構造検査部分と意味評価部分を分離して安定性を測る必要がある。

### 10.3 Adversarial Tests

Adversarial Testsでは、Silent ΔMを意図的に含むケースを作成する。

例として、以下がある。

- 数値だけが微妙に変わる。
- JSON keyが消える。
- 引用が外れる。
- 定義文が弱まる。
- Python function signatureが変わる。
- テストが削除される。
- Generator self_reportが嘘をつく。
- Creative Modeを悪用して保護対象を変更する。

### 10.4 Long-chain Tests

Long-chain Testsでは、20回、50回、100回の編集連鎖においてSilent ΔMが蓄積するか、またOpenAyaneがその蓄積を検出できるかを測定する。これは、生成AIへの長期委任に特有の評価である。

### 10.5 Human Review Calibration

Suspicious Drift判定と人間判断の一致率を測定する。ここで重要なのは、RDEが人間レビューを置き換えることではなく、人間レビューを必要な箇所へ誘導できるかである。

## 11. 評価指標

OpenAyaneの評価指標は、次のように整理できる。

```text
Unauthorized change detection rate
False positive rate
Critical corruption recall
Suspicious drift precision
Human review reduction rate
Rollback success rate
Relation trust calibration correlation
Latency p50 / p95
Audit completeness
Generator self-report mismatch detection rate
Long-chain semantic drift detection rate
```

特に重視すべきは、Critical Corruption Recallである。重大な腐食を見逃すことは、多少のFalse Positiveより危険である。ただし、過剰停止は実用性を損なうため、classificationとrisk_levelを分離し、低リスクのBenign Driftは注記付き承認可能にする。

## 12. 非機能要件

### 12.1 レイテンシ

OpenAyaneのCore処理は高速であるべきである。ただし、すべての評価を10ms以内に収めることは現実的ではない。したがって、Core処理とHeavy Evaluationを分離する。

Core処理に含めるものは、relation lookup、lightweight policy、cached structural checksである。除外するものは、embedding生成、LLM semantic evaluation、full repository scanである。

### 12.2 監査性

すべての承認、停止、差し戻し、ロールバックはAuditLogに残す。Auditは単なるログではなく、意味変化の署名である。

### 12.3 非侵入性

OpenClawまたは外部Agentに統合する場合、公式lifecycle、plugin、hookを優先し、upstream変更に強くする。OpenAyaneは、既存Agent基盤を破壊するのではなく、その実行前後に意味変化評価を追加するレイヤーとして導入されるべきである。

### 12.4 拡張性

Structural Diff Engineはドメインプラグイン化する。Markdown、JSON、PythonはPhase 1対象であり、その後、TypeScript、YAML、SQL、LaTeX、OpenAPI、Terraform、Kubernetes manifestなどへ拡張できる。

## 13. リスクと対策

### 13.1 Semantic Diffの不完全性

意味差分の完全検出は不可能である。したがって、OpenAyaneは完全性ではなく、検出可能性、監査可能性、レビュー誘導を目標とする。

### 13.2 LLM Evaluator依存

RDEをLLM evaluatorに依存させすぎると、Evaluator Driftが生じる。対策として、ルール、スキーマ、AST、型検査、テスト、参照整合性、複数評価器を組み合わせる。

### 13.3 Creative Modeの濫用

Creative Modeでは逸脱が広く許可されるため、保護対象が破壊される危険がある。対策として、Creative Modeでもprotected_elements、source_facts、citation integrity、user intent boundariesを必須にする。

### 13.4 context_affinity poisoning

context_affinityは、現在の変換が関係文脈に属するかを示す重要な指標である。しかし、異常文脈が繰り返し混入すると、文脈適合性自体が汚染される可能性がある。Phase 3以降では、max affinityとmean affinityのhybrid、外れ値検出、分布的更新、履歴分離が必要である。

### 13.5 過剰停止

RDEが過剰に停止を返すと、実用性が下がる。対策として、risk_levelとclassificationを分離し、低リスクのBenign Incidental Driftは注記付き承認可能にする。また、ユーザーや組織ごとにPolicy Profileを設定できるようにする。

### 13.6 履歴参照ループの自己強化リスク

RelationStoreが過去の失敗を参照することは有効だが、その履歴更新が不適切であれば、過剰な不信、過剰停止、特定Generatorへの不当な低評価、文脈境界の過剰固定を生む可能性がある。

したがって、RelationStore更新は、単純な加点・減点ではなく、ドメイン、文書種別、操作モード、レビュー結果、実際の影響度を分離して扱う必要がある。過去の失敗を一般化しすぎることも、失敗を忘却しすぎることも危険である。

## 14. 研究上の意義

OpenAyaneの実装計画は、単なるソフトウェア開発計画ではない。それは、生成AI時代における知的委任の条件を問う研究計画である。

従来のAI安全性は、しばしば危険出力の禁止、拒否応答、コンテンツポリシー、能力制御として設計されてきた。しかし、生成AIが文書、コード、制度、意思決定を継続的に変換する時代には、問題は「危険なことを言ったか」だけではない。問題は、「何をどのように変えたか」「その変化は誰に許可されたか」「その変化はどの関係と制度の中で正当化されるか」である。

RDEは、この問いに対する評価器である。OpenAyaneは、そのRDEを実行・監査・履歴更新・制度接続へ組み込む機構である。両者を区別することで、RDEは文書編集支援、コードレビュー、契約書レビュー、論文査読補助、Agent tool execution監査などへ応用可能な一般評価器となり、OpenAyaneはそれを現実のシステム制御へ接続する機構となる。

OpenAyaneの意義は、生成AIをより賢くすることだけではない。生成AIが何を変えたのか、その変化を誰が引き受けるのかを、制度的に見えるようにすることである。そこに、意味変化の時代における新しいエージェント安全性の核心がある。

## 15. RDE差異検証としての自己評価

本稿自体も、OpenAyane / RDE設計思想および基本設計からの変換結果である。したがって、本稿に対してもRDE的検証が必要である。

### 15.1 保存された要素

保存された要素は、RDEがDiff、Policy、LLM Evaluatorそのものではなく、意味逸脱を裁定する評価構造であるという中核定義である。また、Task Contract、Structural Diff、Semantic Delta、RDE Core、Policy Bridge、Relation Store、Audit Engineという基本構成も保存されている。

### 15.2 変換された要素

元の設計文書は実装設計の性格が強かった。本稿では、それを研究論文として読めるように、問題設定、形式モデル、実装フェーズ、評価計画、研究意義へ再配置した。これはAuthorized Deviationである。

また、今回の更新では、RDEを評価器、OpenAyaneを機構として明示的に分離した。これは元議論の意味を狭めるものではなく、むしろRDEの一般性とOpenAyaneの実行責任を明確化するAuthorized Transformationである。

### 15.3 補完された要素

本稿では、研究論文としての貢献、評価指標、非機能要件、リスク対策、自己RDE検証を補完した。さらに、AuditLog + RelationStore Updateから履歴参照へ戻るループを、OpenAyaneの本質的機構として補完した。

これらは元設計から自然に導かれる拡張であるが、次版では実装データまたはプロトタイプ結果によって検証する必要がある。

### 15.4 未解決の要素

context_affinityの厳密な更新式、Semantic Deltaの信頼性、Human Review Calibrationの具体的データセット、Institution Layerの制度設計は未解決である。本稿では、これらを解決済みとして扱わず、今後の課題として残す。

また、RelationStore更新が自己強化的に過剰停止を生むリスクも未解決である。これには、履歴の重み付け、忘却係数、文脈分離、レビュー結果による補正が必要である。

### 15.5 逸脱リスク

本稿は、設計構想を論文化する過程で、OpenAyaneの実装可能性を強く見せすぎる危険がある。現時点で示されているのは、実装計画と評価設計であり、実証済み性能ではない。したがって、投稿時には「提案アーキテクチャ」「実装計画」「評価プロトコル」として位置づけ、実験結果が未提示であることを明記すべきである。

また、RDEとOpenAyaneを分離したことにより、RDE単体で十分であるかのように読まれるリスクがある。実際には、RDEは評価器であり、実行制御、監査、履歴更新、制度接続にはOpenAyaneのような機構が必要である。

### 15.6 次回更新方針

次回更新では、Phase 1 MVPの仕様をさらに具体化し、TaskContract JSON Schema、RDEResult Schema、MarkdownDiff MVP、PythonAstDiff MVP、Adversarial Test Corpusを付録として追加する。また、可能であれば小規模プロトタイプの実験結果を追加し、提案論文から実証論文へ移行する。

同時に、履歴参照ループについては、RelationStore更新式、drift pattern抽出、generator reliability profile、document fragility profileの初期モデルを明示する必要がある。

## 16. 結論

本稿は、OpenAyaneの実装計画を、RDE評価器を中核とする意味変化監査機構として論文化した。生成AIは保存ではなく再構成する。この性質は創造性の源泉であると同時に、Silent ΔMという危険を生む。したがって、生成AIに必要なのは、変化を禁止する仕組みではなく、変化を分類し、署名し、監査し、必要に応じて停止・差し戻し・ロールバックする構造である。

RDEは意味変化を分類する評価器である。OpenAyaneは、その評価結果をTask Contract、Structural Diff、Semantic Delta、Policy Bridge、Safe Execution Runtime、AuditLog、RelationStore、履歴参照ループへ接続する実行・監査機構である。

今後の課題は、Phase 1 MVPを実装し、Markdown、JSON、Pythonを対象に、Unauthorized Change Detection、Critical Corruption Recall、Generator Self-report Mismatch Detection、Long-chain Semantic Drift Detectionを測定することである。その上で、Semantic Delta、Relation Store、Agent Execution Gate、Institution Layerへ段階的に拡張する。

OpenAyaneの意義は、生成AIをより賢くすることだけではない。生成AIが何を変えたのか、その変化を誰が引き受けるのかを、制度的に見えるようにすることである。そこに、意味変化の時代における新しいエージェント安全性の核心がある。

## 参考文献

Kano, Tomoyuki. 2026. *意味の非収束と共鳴条件：誤配に基づく Resonanceverse の基礎理論*. Version 1.2. Zenodo. DOI: [10.5281/zenodo.20016805](https://doi.org/10.5281/zenodo.20016805).

Lewis, Patrick, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Küttler, et al. 2020. “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.” *Advances in Neural Information Processing Systems*. arXiv:2005.11401.

Ouyang, Long, Jeffrey Wu, Xu Jiang, Diogo Almeida, Carroll L. Wainwright, Pamela Mishkin, Chong Zhang, et al. 2022. “Training Language Models to Follow Instructions with Human Feedback.” *Advances in Neural Information Processing Systems*. arXiv:2203.02155.

Yao, Shunyu, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran, Karthik Narasimhan, and Yuan Cao. 2022. “ReAct: Synergizing Reasoning and Acting in Language Models.” arXiv:2210.03629.

Wilkinson, Mark D., Michel Dumontier, IJsbrand Jan Aalbersberg, Gabrielle Appleton, Myles Axton, Arie Baak, Niklas Blomberg, et al. 2016. “The FAIR Guiding Principles for Scientific Data Management and Stewardship.” *Scientific Data* 3:160018.

