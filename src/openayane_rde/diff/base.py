"""Abstract base class for structural diff engine plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod

from openayane_rde.core.models import GeneratorOutput, StructuralDiff, TaskContract


class StructuralDiffEngine(ABC):
    """Common interface for domain-specific structural diff plugins.

    Each plugin is responsible for a single domain (markdown, json, python, etc.).
    """

    domain: str

    @abstractmethod
    def diff(
        self,
        original: str,
        generated: str,
        contract: TaskContract,
        generator_output: GeneratorOutput | None = None,
    ) -> StructuralDiff:
        """Compute the structural diff between original and generated content.

        Args:
            original: The original content as a string.
            generated: The generated (potentially modified) content as a string.
            contract: The TaskContract defining protected elements and allowed changes.
            generator_output: Optional GeneratorOutput for self-report mismatch detection.

        Returns:
            A StructuralDiff describing the detected changes.
        """
        raise NotImplementedError
