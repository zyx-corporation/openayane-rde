"""Tool call normalization and ExecutionTaskContract building (Phase 3)."""

from __future__ import annotations

import re
from urllib.parse import urlparse
from typing import Any

from openayane_rde.core.models import (
    ExternalSideEffectKind,
    ExecutionActionType,
    ExecutionTaskContract,
    RollbackStrategyKind,
    ToolCallRequest,
    ToolCallRisk,
)

_PATH_KEYS = frozenset({"path", "file", "filename", "filepath", "target_path", "cwd", "file_path"})
_URL_KEYS = frozenset({"url", "endpoint", "uri", "href"})
_SECRET_PATTERNS = re.compile(
    r"(secret|token|api_key|apikey|password|private_key|credential|bearer)\b",
    re.IGNORECASE,
)
_CRITICAL_SHELL = re.compile(
    r"(rm\s+-rf\s+/|curl[^|]*\|\s*sh|wget[^|]*\|\s*sh|sudo\s+rm|git\s+push\s+--force)",
    re.IGNORECASE,
)
_STATE_CHANGING_HINT = re.compile(r"\b(post|put|patch|delete|webhook|publish|submit|send)\b", re.IGNORECASE)


def _first_str(d: dict[str, Any], keys: frozenset[str] | set[str]) -> str | None:
    for k in d:
        if k.lower() in keys and d[k] is not None:
            return str(d[k])
    return None


def infer_target_resources(arguments: dict[str, Any]) -> list[str]:
    """Best-effort resource list from tool arguments."""
    out: list[str] = []
    p = _first_str(arguments, _PATH_KEYS)
    if p:
        out.append(p)
    u = _first_str(arguments, _URL_KEYS)
    if u:
        out.append(u)
    cmd = arguments.get("command")
    if isinstance(cmd, str) and cmd:
        m = re.findall(r"[\w./~+-]+", cmd)
        for token in m[:5]:
            if "/" in token or token.startswith("."):
                out.append(token)
    return list(dict.fromkeys(out))


def normalize_tool_call(req: ToolCallRequest) -> ToolCallRequest:
    """Fill ``target_resources`` when empty using argument heuristics."""
    if req.target_resources:
        return req
    inferred = infer_target_resources(req.arguments)
    return req.model_copy(update={"target_resources": inferred})


def infer_side_effects_for_action(action_type: ExecutionActionType) -> list[str]:
    """Lightweight side-effect labels for auditing."""
    effects: list[str] = []
    if action_type == "read":
        effects.append("read_only_io")
    if action_type in ("write", "delete", "repository_patch"):
        effects.append("filesystem_mutation")
    if action_type in ("network", "external_api"):
        effects.append("network_io")
    if action_type == "execute":
        effects.append("process_execution")
    return effects


def _action_and_strategy(tool_name: str, action_name: str) -> tuple[ExecutionActionType, RollbackStrategyKind]:
    t = f"{tool_name} {action_name}".lower()
    if any(x in t for x in ("read_file", "list_dir", "glob", "grep", "cat ")):
        return "read", "none"
    if "network" in t or "http" in t or "fetch" in t:
        return "network", "none"
    if "api" in t or "webhook" in t:
        return "external_api", "manual"
    if any(x in t for x in ("write", "apply_patch", "edit", "save")):
        return "write", "file_snapshot"
    if "delete" in t or "remove" in t or "unlink" in t:
        return "delete", "file_snapshot"
    if any(x in t for x in ("bash", "shell", "run_terminal", "exec", "subprocess")):
        return "execute", "manual"
    if "git" in t and "patch" in t:
        return "repository_patch", "git_patch_reverse"
    return "unknown", "none"


def build_execution_task_contract(req: ToolCallRequest) -> ExecutionTaskContract:
    """Map a normalized tool call to an execution contract."""
    req = normalize_tool_call(req)
    action_type, rollback_strategy = _action_and_strategy(req.tool_name, req.action_name)
    targets = req.target_resources
    protected: list[str] = []
    forbidden: list[str] = []
    allowed: list[str] = []
    expected = infer_side_effects_for_action(action_type)
    network_allowed = action_type in ("network", "external_api")
    external_kind = _infer_external_side_effect_kind(req.arguments, action_type)
    allowed_domains = _infer_allowed_domains(req.arguments)
    return ExecutionTaskContract(
        source_tool_call_id=req.tool_call_id,
        agent_id=req.agent_id,
        action_type=action_type,
        tool_name=req.tool_name,
        target_resources=targets,
        expected_side_effects=expected,
        allowed_side_effects=allowed,
        forbidden_side_effects=forbidden,
        protected_resources=protected,
        rollback_strategy=rollback_strategy,
        network_allowed=network_allowed,
        external_side_effect_kind=external_kind,
        allowed_network_domains=allowed_domains,
    )


def _infer_allowed_domains(arguments: dict[str, Any]) -> list[str]:
    raw = arguments.get("allowed_domains")
    if not isinstance(raw, list):
        return []
    return [str(d).strip().lower() for d in raw if str(d).strip()]


def _infer_external_side_effect_kind(
    arguments: dict[str, Any], action_type: ExecutionActionType
) -> ExternalSideEffectKind:
    if action_type not in ("network", "external_api"):
        return "none"
    blob = str(arguments).lower()
    if any(k in blob for k in ("payment", "billing", "invoice", "charge")):
        return "payment_or_billing"
    if any(k in blob for k in ("auth", "oauth", "login", "token_refresh")):
        return "identity_or_auth"
    if any(k in blob for k in ("exfiltrate", "upload_dump", "dump_all", "backup_export")):
        return "data_exfiltration_risk"
    if any(k in blob for k in ("publish", "release", "post_message")):
        return "publishing"
    if any(k in blob for k in ("notify", "notification", "webhook")):
        return "notification"
    method = str(arguments.get("method", "")).lower()
    if method in {"post", "put", "patch", "delete"} or _STATE_CHANGING_HINT.search(blob):
        return "state_changing_request"
    if method in {"get", "head"}:
        return "read_only_fetch"
    if _first_str(arguments, _URL_KEYS):
        return "read_only_fetch"
    return "unknown"


def score_tool_call_risk(
    contract: ExecutionTaskContract,
    *,
    protected_resource_paths: list[str] | None = None,
    raw_arguments: dict[str, Any] | None = None,
) -> ToolCallRisk:
    """Rule-based risk scoring (Phase 3 spec §8.3 / §11)."""
    reasons: list[str] = []
    protected = protected_resource_paths or []
    unknown_target = len(contract.target_resources) == 0 and contract.action_type in (
        "write",
        "delete",
        "execute",
        "unknown",
    )
    protected_touch = any(
        t and any(t.startswith(p) or p in t for p in protected) for t in contract.target_resources
    )
    external = contract.action_type in ("network", "external_api")
    args_blob = (
        str(raw_arguments).lower()
        if raw_arguments is not None
        else str(contract.model_dump()).lower()
    )
    if _SECRET_PATTERNS.search(args_blob):
        return ToolCallRisk(
            risk_level="critical",
            risk_score=1.0,
            irreversible=True,
            external_side_effect=external,
            protected_resource_touched=protected_touch,
            rollback_possible=False,
            unknown_target=unknown_target,
            reasons=reasons + ["credential_or_secret_context_detected"],
        )
    if contract.action_type == "execute":
        cmd = ""
        if isinstance(raw_arguments, dict):
            cmd = str(raw_arguments.get("command", "") or raw_arguments.get("cmd", ""))
        if _CRITICAL_SHELL.search(cmd):
            return ToolCallRisk(
                risk_level="critical",
                risk_score=0.98,
                irreversible=True,
                external_side_effect=False,
                protected_resource_touched=protected_touch,
                rollback_possible=False,
                unknown_target=unknown_target,
                reasons=reasons + ["critical_shell_pattern"],
            )
        return ToolCallRisk(
            risk_level="high",
            risk_score=0.82,
            irreversible=False,
            external_side_effect=False,
            protected_resource_touched=protected_touch,
            rollback_possible=contract.rollback_strategy not in ("none",),
            unknown_target=unknown_target,
            reasons=reasons + ["shell_execution"],
        )
    if unknown_target:
        reasons.append("unknown_target")
        return ToolCallRisk(
            risk_level="high",
            risk_score=0.75,
            irreversible=False,
            external_side_effect=external,
            protected_resource_touched=False,
            rollback_possible=False,
            unknown_target=True,
            reasons=reasons,
        )
    if protected_touch:
        reasons.append("protected_resource")
        return ToolCallRisk(
            risk_level="high",
            risk_score=0.78,
            irreversible=False,
            external_side_effect=external,
            protected_resource_touched=True,
            rollback_possible=contract.rollback_strategy == "file_snapshot",
            unknown_target=False,
            reasons=reasons,
        )
    if external:
        kind = contract.external_side_effect_kind
        reasons.append(f"external_side_effect:{kind}")
        if kind == "data_exfiltration_risk":
            return ToolCallRisk(
                risk_level="critical",
                risk_score=0.97,
                irreversible=True,
                external_side_effect=True,
                protected_resource_touched=False,
                rollback_possible=False,
                unknown_target=False,
                reasons=reasons,
            )
        if kind == "payment_or_billing":
            return ToolCallRisk(
                risk_level="critical",
                risk_score=0.95,
                irreversible=True,
                external_side_effect=True,
                protected_resource_touched=False,
                rollback_possible=False,
                unknown_target=False,
                reasons=reasons,
            )
        if kind in ("state_changing_request", "notification", "publishing", "identity_or_auth"):
            return ToolCallRisk(
                risk_level="high",
                risk_score=0.82,
                irreversible=True,
                external_side_effect=True,
                protected_resource_touched=False,
                rollback_possible=False,
                unknown_target=False,
                reasons=reasons,
            )
        if kind == "unknown":
            return ToolCallRisk(
                risk_level="high",
                risk_score=0.76,
                irreversible=True,
                external_side_effect=True,
                protected_resource_touched=False,
                rollback_possible=False,
                unknown_target=False,
                reasons=reasons,
            )
        url = _first_str(raw_arguments or {}, _URL_KEYS) if raw_arguments is not None else None
        if url and _SECRET_PATTERNS.search(url):
            return ToolCallRisk(
                risk_level="critical",
                risk_score=1.0,
                irreversible=True,
                external_side_effect=True,
                protected_resource_touched=False,
                rollback_possible=False,
                unknown_target=False,
                reasons=reasons + ["credential_in_url"],
            )
        if kind == "read_only_fetch":
            domain_ok = _domain_allowed(url, contract.allowed_network_domains)
            if not domain_ok:
                return ToolCallRisk(
                    risk_level="high",
                    risk_score=0.72,
                    irreversible=False,
                    external_side_effect=True,
                    protected_resource_touched=False,
                    rollback_possible=False,
                    unknown_target=False,
                    reasons=reasons + ["domain_not_allowlisted"],
                )
            return ToolCallRisk(
                risk_level="medium",
                risk_score=0.5,
                irreversible=False,
                external_side_effect=True,
                protected_resource_touched=False,
                rollback_possible=False,
                unknown_target=False,
                reasons=reasons + ["allowlisted_read_only_fetch"],
            )
        return ToolCallRisk(
            risk_level="high",
            risk_score=0.72,
            irreversible=True,
            external_side_effect=True,
            protected_resource_touched=False,
            rollback_possible=False,
            unknown_target=False,
            reasons=reasons,
        )
    if contract.action_type in ("delete",):
        return ToolCallRisk(
            risk_level="high",
            risk_score=0.68,
            irreversible=True,
            external_side_effect=False,
            protected_resource_touched=protected_touch,
            rollback_possible=contract.rollback_strategy == "file_snapshot",
            unknown_target=unknown_target,
            reasons=reasons + ["delete_operation"],
        )
    if contract.action_type == "write":
        return ToolCallRisk(
            risk_level="medium",
            risk_score=0.45,
            irreversible=False,
            external_side_effect=False,
            protected_resource_touched=protected_touch,
            rollback_possible=contract.rollback_strategy == "file_snapshot",
            unknown_target=False,
            reasons=reasons + ["local_write"],
        )
    return ToolCallRisk(
        risk_level="low",
        risk_score=0.15,
        irreversible=False,
        external_side_effect=False,
        protected_resource_touched=False,
        rollback_possible=True,
        unknown_target=False,
        reasons=reasons + ["read_or_low_impact"],
    )


def _domain_allowed(url: str | None, allowed_domains: list[str]) -> bool:
    if not url:
        return False
    if not allowed_domains:
        return False
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return any(host == d or host.endswith(f".{d}") for d in allowed_domains)
