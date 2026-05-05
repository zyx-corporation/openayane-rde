---
title: "OpenAyane RDE Phase 4 完了レポート"
version: "0.1"
date: "2026-05-05"
status: "completion-record"
---

# OpenAyane RDE Phase 4 完了レポート

## 0. 目的

本書は、**Phase 4: Institution and Accountability Layer** の実装・文書・テストが、リポジトリ上どこまで完了したかを **出口記録** として固定する。

- Phase 4 を「高保証の本番制度インフラ」と誤読しないための **成熟度の上限** を明示する。
- Phase 5（運用化）へ引き継ぐ **入力成果物** を列挙する。
- 主要 Issue / 設計ノート / コード配置の対応を後追い可能にする。

**正典となる設計文書:** [`40_openayane_rde_phase4_institution_bridge_spec.md`](40_openayane_rde_phase4_institution_bridge_spec.md)、[`41_openayane_rde_phase3_to_phase4_evidence_handoff.md`](41_openayane_rde_phase3_to_phase4_evidence_handoff.md)。

## 1. 完了宣言

```text
Phase 4 ステータス: 開発計画 §7.4 の完了条件を満たす実装・接続・テストまで到達（MVP + 接続）
成熟度: 制度ブリッジ・権限スケルトン・監査分離は利用可能。PoP / 二者承認実行エンジンは未実装
本番宣言: なし（仕様 doc/40 の Out of scope に従う）
Phase 5: 着手可能（docs/50、GitHub #44〜#54）
```

Phase 4 は **RDE の意味評価を置き換えない** 前提で、Policy / 実行ゲート / Phase 1 評価フローに **任意の制度オーバーレイ** を載せられる状態になった。

## 2. 実装スコープ（コード）

```text
src/openayane_rde/institution/
  - models.py          InstitutionRule, AuthorityRef, ReviewerAuthority,
                       EvidenceHandoff, InstitutionalDecision, HaltProvenance
  - policy.py          first_matching_rule, HandoffDecisionInput, 権限・不可逆ヘルパ
  - bridge.py          DeterministicInstitutionBridge（build_handoff / decide）
  - rule_registry.py   InstitutionRuleRegistry
  - authority.py       Permission, ActorRole, ApprovalStep, ApprovalChain
  - pop_uid.py         PopUidAdapter（Protocol）
  - accountability.py  DecisionProvenance, provenance_from_policy_decision

src/openayane_rde/policy/institution_bridge.py
  - decide_policy_with_institution

src/openayane_rde/runtime/_flow.py
  - run_phase1_evaluation* の任意制度オプション（registry + action/side_effect + PoP）

src/openayane_rde/agent/execution_gate.py
  - evaluate_before_execution の任意 institution_registry / PoP、ゲート決定への制度フィールド

src/openayane_rde/core/models.py
  - PolicyDecision: institution_rule_id, institutional_rationale
  - ExecutionGateDecision: institution_rule_id, institutional_rationale

src/openayane_rde/audit/log.py
  - audit_event_policy_decision（RDE 分類と institution をペイロードで分離）
  - audit_event_execution_gate_evaluated に制度フィールドを含める
```

## 3. Issue・テーマ対応（代表）

| 区分 | Issue / テーマ | 内容 |
|------|----------------|------|
| P4-1 | #27 | InstitutionRule / AuthorityRef / ReviewerAuthority モデル |
| P4-2 | #28 | EvidenceHandoff / InstitutionalDecision |
| P4-3 | #29 | HaltProvenance（policy halt と RDE halt の区別） |
| P4-4 | #30 | DeterministicInstitutionBridge（MVP） |
| P4-5 | #31 | 権限・不可逆・halt / handoff の回帰テスト |
| P4-6 | #32 | Phase 3→4 エビデンス・ハンドオフ設計ノート（doc/41 系） |
| ハンドオフ整合 | #41 | build_handoff を docs/41 に整合（evidence_basis / 監査ギャップ注記 / rollback 相関） |
| 計画 §7.2 系 | #51 | PolicyDecision 参照、レジストリ、authority、PoP I/F、監査分離 |
| ランタイム接続 | #55 | Phase 1 フロー・実行ゲートへのオプション統合 |
| 境界テスト補完 | #57 / PR #58 | 不可逆受理、rollback のみ注記、registry.register、Provenance PoP、ApprovalChain、監査 null 等 |

詳細な PR 履歴は GitHub の各 Issue / マージコミットを参照。

## 4. 開発計画 §7.4 完了条件の照合

| 条件 | 状態 | 根拠 |
|------|------|------|
| PolicyDecision が InstitutionRule を参照できる | 満たす | `institution_rule_id` / `institutional_rationale`、および `decide_policy_with_institution` |
| actor / role / permission / approval chain を表現できる | 満たす（スケルトン） | `authority.py`、ReviewerAuthority は既存 |
| PoP-UID adapter interface が定義されている | 満たす | `PopUidAdapter` Protocol（実装は呼び出し側） |
| 承認・却下・停止の根拠を AuditLog に残せる | 満たす（ヘルパ） | `audit_event_policy_decision`、ゲート監査ペイロード拡張 |
| RDE 分類と制度判断を混同しない | 満たす（設計・コード） | Provenance、監査ペイロードの `rde_classification` 分離、doc/40 原則 |

## 5. テスト・品質

- **単体・統合:** `tests/unit/test_institution_*.py`、`test_phase4_*.py`、`test_audit_log.py`（該当箇所）など。
- **境界:** 証跡なし・不可逆不明・ルール不整合、PoP 失敗、rollback のみの制度注記、registry 順序などを追加済み（#57 系）。
- **CI:** `pytest`、`ruff`、`mypy`（リポジトリ標準ワークフロー）。

## 6. 意図的に範囲外としたもの（doc/40 と整合）

```text
- 完全な PoP-UID / 本番 IdP 連携
- 暗号学的監査ログ
- 承認チェーンの自動充足エンジン（ApprovalChain は表現のみ）
- 本番 Web UI / DAO 投票
- 制度ルールの法適合エンジン
```

これらは **Phase 5 以降または明示的な昇格** まで手を付けない。

## 7. Phase 5 への引き継ぎ

- **運用化の正典:** [`50_openayane_rde_phase5_operational_hardening_spec.md`](50_openayane_rde_phase5_operational_hardening_spec.md)。
- **作業 Issue:** GitHub [#44](https://github.com/zyx-corporation/openayane-rde/issues/44) 〜 [#54](https://github.com/zyx-corporation/openayane-rde/issues/54)。実行順は **§17**（API #46 は最後）。
- **プロジェクト管理（日本語）:** [`01_project_management_ja.md`](01_project_management_ja.md) §13。

Phase 4 の成果は、CLI / 設定 / 監査閲覧コマンドなどから **同じ Policy / Institution / Audit 境界を呼び出す** 形で消費される想定である。

## 8. 文書履歴

| Version | Date | Note |
|---------|------|------|
| 0.1 | 2026-05-05 | 初版。Phase 4 MVP + ランタイム接続 + テスト補完までを完了記録として固定。 |
