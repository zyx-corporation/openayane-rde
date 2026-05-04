"""TaskContract builder for Phase 1.

Phase 1: rule-based builder from explicit parameters.
Full automatic intent-to-contract conversion is not required.
"""

from __future__ import annotations

from openayane_rde.contract.schema import default_output_policy, default_review_policy
from openayane_rde.core.models import (
    ContractMode,
    OutputPolicy,
    ProtectedElementKind,
    ReviewPolicy,
    TargetScope,
    TaskContract,
)


def build_contract(
    mode: ContractMode,
    requested_action: str,
    files: list[str] | None = None,
    symbols: list[str] | None = None,
    sections: list[str] | None = None,
    allowed_delta_m: list[str] | None = None,
    forbidden_delta_m: list[str] | None = None,
    protected_elements: list[ProtectedElementKind] | None = None,
    output_policy: OutputPolicy | None = None,
    review_policy: ReviewPolicy | None = None,
    metadata: dict[str, object] | None = None,
) -> TaskContract:
    """Build a TaskContract from explicit parameters.

    Args:
        mode: Contract mode (preservation, creative, refactor, research, execution).
        requested_action: Description of the requested transformation.
        files: Target file paths.
        symbols: Target code symbols.
        sections: Target document sections.
        allowed_delta_m: Explicitly permitted semantic changes.
        forbidden_delta_m: Explicitly prohibited semantic changes.
        protected_elements: Elements that must not be changed.
        output_policy: Output policy (defaults to require_patch=True).
        review_policy: Review policy (defaults to strict preservation policy).

    Returns:
        A validated TaskContract.
    """
    return TaskContract(
        mode=mode,
        target_scope=TargetScope(
            files=files or [],
            symbols=symbols or [],
            sections=sections or [],
        ),
        requested_action=requested_action,
        allowed_delta_m=allowed_delta_m or [],
        forbidden_delta_m=forbidden_delta_m or [],
        protected_elements=protected_elements or [],
        output_policy=output_policy or default_output_policy(),
        review_policy=review_policy or default_review_policy(),
        metadata=metadata or {},
    )
