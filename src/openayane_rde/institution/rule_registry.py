"""Normative registry for :class:`~openayane_rde.institution.models.InstitutionRule`.

Deterministic rule ordering is preserved (first registration wins for matching).
"""

from __future__ import annotations

from collections.abc import Sequence

from openayane_rde.core.models import ExecutionActionType, ExternalSideEffectKind
from openayane_rde.institution.models import InstitutionRule
from openayane_rde.institution.policy import first_matching_rule


class InstitutionRuleRegistry:
    """Ordered collection of :class:`InstitutionRule` records for lookup."""

    __slots__ = ("_rules",)

    def __init__(self, rules: Sequence[InstitutionRule] | None = None) -> None:
        self._rules: list[InstitutionRule] = list(rules) if rules else []

    def register(self, rule: InstitutionRule) -> None:
        """Append a rule (later entries remain consultable but matching is first-hit)."""

        self._rules.append(rule)

    @property
    def rules(self) -> list[InstitutionRule]:
        return list(self._rules)

    def first_match(
        self,
        *,
        action_type: ExecutionActionType,
        side_effect: ExternalSideEffectKind,
    ) -> InstitutionRule | None:
        """First rule applying to both dimensions (deterministic list order)."""

        return first_matching_rule(
            self._rules,
            action_type=action_type,
            side_effect=side_effect,
        )
