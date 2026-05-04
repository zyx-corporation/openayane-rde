"""Intent Parser stub for Phase 1.

Full intent parsing is out of scope for Phase 1.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ActionType = Literal[
    "edit_document", "modify_code", "run_tool", "summarize", "refactor", "research"
]
RiskHintStr = Literal["low", "medium", "high", "critical"]


@dataclass
class Intent:
    action_type: ActionType
    target: str
    risk_hint: RiskHintStr
    raw_instruction: str


def parse_intent(raw_instruction: str) -> Intent:
    """Phase 1 stub: returns a generic edit_document intent.

    Full NLU-based intent extraction is not implemented in Phase 1.
    """
    return Intent(
        action_type="edit_document",
        target="unknown",
        risk_hint="medium",
        raw_instruction=raw_instruction,
    )
