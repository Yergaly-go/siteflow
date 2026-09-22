import pytest

from ai_core import CandidateEvidenceExtractor, CandidateExtractionInput, RequirementInput, SourceProvenance
from ai_core.errors import AIError, AIErrorCode
from ai_core.providers import NoAIProvider


def test_no_ai_provider_returns_controlled_unavailable_without_business_state():
    extraction_input = CandidateExtractionInput(
        work_item_id="WORK-1",
        requirements=[RequirementInput(requirement_id="REQ-1", text="Photo")],
        source_type="text/plain",
        source_content="Photo supplied.",
        source_provenance=SourceProvenance(source_id="SRC-1"),
    )
    before = extraction_input.model_dump()
    with pytest.raises(AIError) as captured:
        CandidateEvidenceExtractor(NoAIProvider()).extract_candidates(extraction_input)
    assert captured.value.code == AIErrorCode.UNAVAILABLE
    assert extraction_input.model_dump() == before
    assert "workflow_status" not in extraction_input.model_dump()


def test_no_ai_provider_exposes_no_acceptance_operation():
    provider = NoAIProvider()
    assert not hasattr(provider, "validate_evidence")
    assert not hasattr(provider, "confirm_work_item")
    assert not hasattr(provider, "unlock_next_stage")
