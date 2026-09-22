from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel


class AIProvider(Protocol):
    def generate_structured(
        self,
        *,
        task: str,
        input_data: dict,
        output_schema: type[BaseModel],
    ) -> BaseModel: ...


class ProviderError(Exception):
    """Base exception kept inside the provider adapter boundary."""


class ProviderTimeoutError(ProviderError):
    pass


class ProviderUnavailableError(ProviderError):
    pass


class ProviderAuthError(ProviderError):
    pass


class ProviderFailureError(ProviderError):
    pass
