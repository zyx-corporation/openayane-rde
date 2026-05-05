"""Pydantic schema for ``openayane.toml``.

Defaults match ``docs/50_openayane_rde_phase5_operational_hardening_spec.md`` §7.1.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, PositiveInt

RelationStoreBackend = Literal["json", "sqlite"]


class ProfileSection(BaseModel):
    """Operational profile label and mode."""

    model_config = {"extra": "forbid"}

    name: str = Field(default="local-dev", description="Profile name for audit and logs.")
    mode: str = Field(
        default="internal-pilot",
        description="Deployment or trust mode (operational metadata only).",
    )


class AuditSection(BaseModel):
    model_config = {"extra": "forbid"}

    path: str = Field(
        default=".openayane/audit.jsonl",
        description="Audit JSONL path (relative paths are resolved against the config file).",
    )
    append: bool = Field(default=True, description="Append to existing audit log when true.")


class RelationStoreSection(BaseModel):
    model_config = {"extra": "forbid"}

    backend: RelationStoreBackend = Field(
        default="json",
        description="RelationStore backend identifier.",
    )
    path: str = Field(
        default=".openayane/relation.sqlite3",
        description="Store path (JSON dir or SQLite file, depending on backend).",
    )


class RuntimeSection(BaseModel):
    model_config = {"extra": "forbid"}

    workspace_root: str = Field(
        default=".",
        description="Workspace root for local adapters and path resolution.",
    )
    allow_subprocess_execution: bool = Field(
        default=False,
        description="Must remain false unless explicitly enabled by operators.",
    )
    max_output_bytes: PositiveInt = Field(
        default=64000,
        description="Upper bound on captured generator output size for local runs.",
    )


class PolicySection(BaseModel):
    model_config = {"extra": "forbid"}

    halt_on_critical_risk: bool = Field(default=True)
    allow_auto_execute_low_risk: bool = Field(default=True)


class InstitutionSection(BaseModel):
    model_config = {"extra": "forbid"}

    rules_path: str = Field(
        default=".openayane/institution_rules.json",
        description="Institution rule fixture path.",
    )
    authority_path: str = Field(
        default=".openayane/reviewer_authority.json",
        description="Reviewer authority fixture path.",
    )


class OpenAyaneConfig(BaseModel):
    """Root configuration object for Phase 5 local operations."""

    model_config = {"extra": "forbid"}

    profile: ProfileSection = Field(default_factory=ProfileSection)
    audit: AuditSection = Field(default_factory=AuditSection)
    relation_store: RelationStoreSection = Field(default_factory=RelationStoreSection)
    runtime: RuntimeSection = Field(default_factory=RuntimeSection)
    policy: PolicySection = Field(default_factory=PolicySection)
    institution: InstitutionSection = Field(default_factory=InstitutionSection)
