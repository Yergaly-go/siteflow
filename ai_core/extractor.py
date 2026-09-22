from __future__ import annotations

from pydantic import ValidationError

from .contracts import CandidateEvidence, CandidateEvidenceBatch, CandidateExtractionInput
from .errors import AIError, AIErrorCode
from .prompts import CANDIDATE_EVIDENCE_TASK
from .providers.base import (
    AIProvider,
    ProviderAuthError,
    ProviderError,
    ProviderFailureError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from .validation import validate_candidate_batch


class CandidateEvidenceExtractor:
    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    def extract_candidates(self, input: CandidateExtractionInput) -> list[CandidateEvidence]:
        input_data = input.model_dump(mode="json")
        try:
            provider_output = self.provider.generate_structured(
                task=CANDIDATE_EVIDENCE_TASK,
                input_data=input_data,
                output_schema=CandidateEvidenceBatch,
            )
        except ProviderTimeoutError as error:
            raise AIError(AIErrorCode.TIMEOUT, "AI provider timed out") from error
        except ProviderUnavailableError as error:
            raise AIError(AIErrorCode.UNAVAILABLE, "AI provider is unavailable") from error
        except ProviderAuthError as error:
            raise AIError(AIErrorCode.AUTH_ERROR, "AI provider authentication failed") from error
        except ProviderFailureError as error:
            raise AIError(AIErrorCode.PROVIDER_ERROR, "AI provider failed") from error
        except ProviderError as error:
            raise AIError(AIErrorCode.PROVIDER_ERROR, "AI provider error") from error
        except ValidationError as error:
            raise AIError(AIErrorCode.SCHEMA_ERROR, "AI provider output failed schema validation") from error
        except Exception as error:
            raise AIError(AIErrorCode.PROVIDER_ERROR, "Unexpected AI provider error") from error

        if not isinstance(provider_output, CandidateEvidenceBatch):
            try:
                provider_output = CandidateEvidenceBatch.model_validate(provider_output)
            except ValidationError as error:
                raise AIError(AIErrorCode.SCHEMA_ERROR, "AI provider output failed schema validation") from error
            except (TypeError, ValueError) as error:
                raise AIError(AIErrorCode.INVALID_OUTPUT, "AI provider returned an invalid output type") from error

        validate_candidate_batch(provider_output, input)
        return provider_output.candidates
