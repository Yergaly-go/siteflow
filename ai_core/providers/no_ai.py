from __future__ import annotations

from pydantic import BaseModel

from .base import ProviderUnavailableError


class NoAIProvider:
    """Explicit provider for deployments where AI is disabled or unavailable."""

    def generate_structured(
        self,
        *,
        task: str,
        input_data: dict,
        output_schema: type[BaseModel],
    ) -> BaseModel:
        raise ProviderUnavailableError("AI is disabled")
