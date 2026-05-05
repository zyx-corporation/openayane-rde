"""Actor roles, permissions, and approval chains (Phase 4 accountability scaffolding).

These models express organizational structure; they are not cryptographic proof of identity.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Permission(BaseModel):
    """Named capability within an institution (coarse-grained)."""

    permission_id: str = Field(min_length=1)
    description: str = ""
    resource_patterns: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class ActorRole(BaseModel):
    """Maps an organizational role to permission identifiers."""

    role_id: str = Field(min_length=1)
    name: str
    permission_ids: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class ApprovalStep(BaseModel):
    """One step in a multi-party approval chain."""

    order: int = Field(ge=0)
    role_id: str = Field(min_length=1)
    required_approvals: int = Field(default=1, ge=1)

    model_config = {"extra": "forbid"}


class ApprovalChain(BaseModel):
    """Ordered approval sequence (e.g. dual control)."""

    chain_id: str = Field(min_length=1)
    name: str
    steps: list[ApprovalStep] = Field(default_factory=list)

    model_config = {"extra": "forbid"}
