import pytest
from pydantic import BaseModel

from ai_core import CandidateEvidenceExtractor, CandidateExtractionInput, RequirementInput, SourceProvenance
from ai_core.errors import AIError, AIErrorCode
from ai_core.providers.base import ProviderAuthError, ProviderFailureError


class RaisingProvider:
    def __init__(self, error):
        self.error = error

    def generate_structured(self, *, task: str, input_data: dict, output_schema: type[BaseModel]) -> BaseModel:
        raise self.error


class RawProvider:
    def __init__(self, value):
        self.value = value

    def generate_structured(self, *, task: str, input_data: dict, output_schema: type[BaseModel]) -> BaseModel:
        return self.value


def extraction_input():
    return CandidateExtractionInput(
        work_item_id="WORK-1",
        requirements=[RequirementInput(requirement_id="REQ-1", text="Photo")],
        source_type="text/plain",
        source_content="Photo exists.",
        source_provenance=SourceProvenance(source_id="SRC-1"),
    )


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (ProviderAuthError("denied"), AIErrorCode.AUTH_ERROR),
        (ProviderFailureError("failed"), AIErrorCode.PROVIDER_ERROR),
        (RuntimeError("unexpected"), AIErrorCode.PROVIDER_ERROR),
    ],
)
def test_provider_exceptions_are_normalized(error, code):
    with pytest.raises(AIError) as captured:
        CandidateEvidenceExtractor(RaisingProvider(error)).extract_candidates(extraction_input())
    assert captured.value.code == code
    assert type(captured.value.__cause__) is type(error)


@pytest.mark.parametrize(
    "value",
    [
        "malformed",
        {"candidates": [{"requirement_id": "REQ-1"}]},
        {"candidates": [], "confirmed": True},
        {
            "candidates": [{
                "requirement_id": "REQ-1", "source_id": "SRC-1", "source_type": "text/plain",
                "reference": None, "excerpt": "Photo exists.", "interpretation": "Potential match.",
                "uncertainty": "certain",
            }]
        },
    ],
)
def test_malformed_or_schema_invalid_output_is_rejected(value):
    with pytest.raises(AIError) as captured:
        CandidateEvidenceExtractor(RawProvider(value)).extract_candidates(extraction_input())
    assert captured.value.code in {AIErrorCode.INVALID_OUTPUT, AIErrorCode.SCHEMA_ERROR}
