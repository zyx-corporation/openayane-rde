"""Generator interface definition.

Phase 1: real LLM API integration is not required.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from openayane_rde.core.models import GeneratorOutput, TaskContract


class GeneratorAdapter(ABC):
    """Abstract interface for Generator adapters."""

    @abstractmethod
    def generate(self, contract: TaskContract, original: str) -> GeneratorOutput:
        """Generate output for a given TaskContract and original content."""
        raise NotImplementedError
