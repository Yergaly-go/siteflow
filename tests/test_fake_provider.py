import pytest

from ai_core import CandidateEvidenceExtractor, CandidateExtractionInput, RequirementInput, SourceProvenance
from ai_core.errors import AIError, AIErrorCode
from ai_core.providers import FakeProvider


def input_value():
    return CandidateExtractionInput(
        work_item_id="WORK-1",
        requirements=[RequirementInput(requirement_id="REQ-1", text="Photo")],
        source_type="message",
        source_content="Photo at axis A-12.",
        source_provenance=SourceProvenance(source_id="SRC-1"),
    )


@pytest.mark.parametrize(
    "mode",
    ["valid_candidate", "zero_candidates", "ambiguous_candidate", "conflicting_candidate", "unsupported_candidate"],
)
def test_fake_provider_modes_are_deterministic(mode):
    extractor = CandidateEvidenceExtractor(FakeProvider(mode))
    first = extractor.extract_candidates(input_value())
    second = extractor.extract_candidates(input_value())
    assert first == second


def test_fake_provider_never_pretends_to_be_live_ai():
    provider = FakeProvider()
    assert provider.__class__.__name__ == "FakeProvider"
    assert not hasattr(provider, "api_key")


@pytest.mark.parametrize(
    ("mode", "code"),
    [
        ("timeout", AIErrorCode.TIMEOUT),
        ("unavailable", AIErrorCode.UNAVAILABLE),
        ("provider_failure", AIErrorCode.PROVIDER_ERROR),
        ("invalid_output", AIErrorCode.SCHEMA_ERROR),
    ],
)
def test_fake_provider_failure_modes_are_normalized(mode, code):
    with pytest.raises(AIError) as captured:
        CandidateEvidenceExtractor(FakeProvider(mode)).extract_candidates(input_value())
    assert captured.value.code == code
