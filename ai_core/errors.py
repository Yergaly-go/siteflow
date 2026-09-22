from __future__ import annotations

from enum import StrEnum


class AIErrorCode(StrEnum):
    TIMEOUT = "AI_TIMEOUT"
    UNAVAILABLE = "AI_UNAVAILABLE"
    AUTH_ERROR = "AI_AUTH_ERROR"
    INVALID_OUTPUT = "AI_INVALID_OUTPUT"
    SCHEMA_ERROR = "AI_SCHEMA_ERROR"
    PROVIDER_ERROR = "AI_PROVIDER_ERROR"


class AIError(Exception):
    """Normalized error exposed to a future integration layer."""

    def __init__(self, code: AIErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class AICandidateValidationError(AIError):
    def __init__(self, message: str) -> None:
        super().__init__(AIErrorCode.INVALID_OUTPUT, message)
