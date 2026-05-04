"""Mock generator for deterministic test outputs.

Phase 1: used in tests to provide fixture GeneratorOutput objects without
real LLM API calls.
"""

from __future__ import annotations

from openayane_rde.core.models import GeneratorOutput, ModelInfo, SelfReport, TaskContract
from openayane_rde.generator.adapter import GeneratorAdapter


class MockGenerator(GeneratorAdapter):
    """Returns a fixed payload with a configurable self_report."""

    def __init__(
        self,
        payload: str,
        self_report: SelfReport | None = None,
        model: str = "manual-test-generator",
    ) -> None:
        self._payload = payload
        self._self_report = self_report or SelfReport()
        self._model = model

    def generate(self, contract: TaskContract, original: str) -> GeneratorOutput:
        return GeneratorOutput(
            contract_id=contract.contract_id,
            output_type="full_text",
            payload=self._payload,
            self_report=self._self_report,
            model_info=ModelInfo(provider="mock", model=self._model),
        )
