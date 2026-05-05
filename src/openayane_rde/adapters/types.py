"""Adapter protocol and shared operational types (Phase 5)."""

from __future__ import annotations

from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from openayane_rde.core.models import AuditEvent, ExecutionTaskContract, TaskContract
from openayane_rde.runtime.result import Phase1EvaluationResult


class AdapterSideEffectProfile(BaseModel):
    """Declared side-effect posture for an adapter (defaults: read-only, local)."""

    model_config = {"extra": "forbid"}

    may_read_filesystem: bool = True
    may_write_filesystem: bool = False
    may_use_network: bool = False


class FilesystemAdapterSource(BaseModel):
    """Read text files under ``root``; no writes."""

    model_config = {"extra": "forbid"}

    kind: Literal["filesystem"] = "filesystem"
    root: str
    relative_paths: list[str] = Field(
        default_factory=list,
        description="Paths relative to root; empty means no files collected.",
    )
    requested_action: str = Field(
        default="Evaluate local files under OpenAyane TaskContract.",
    )
    domain: Literal["markdown", "json", "python"] = "markdown"


class AdapterContext(BaseModel):
    """Normalized context after collection (evidence-oriented, not RDE output)."""

    model_config = {"extra": "forbid"}

    source_kind: str
    files: dict[str, str] = Field(default_factory=dict)
    notes: list[str] = Field(
        default_factory=list,
        description="Explicit missing-evidence or collection caveats.",
    )
    domain: Literal["markdown", "json", "python"] = "markdown"
    requested_action: str


@runtime_checkable
class OpenAyaneAdapter(Protocol):
    """Operational adapter: collect → contract → audit evidence from evaluation."""

    @property
    def side_effect_profile(self) -> AdapterSideEffectProfile: ...

    def collect_context(self, source: FilesystemAdapterSource) -> AdapterContext: ...

    def build_contract(self, context: AdapterContext) -> TaskContract | ExecutionTaskContract: ...

    def produce_evidence(self, result: Phase1EvaluationResult) -> AuditEvent: ...
