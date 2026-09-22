import pytest

from ai_core import CandidateEvidenceExtractor, CandidateExtractionInput, RequirementInput, SourceProvenance
from ai_core.errors import AIError, AIErrorCode
from ai_core.providers import FakeProvider


def make_input(content="Фото оси А-12.", reference="doc:42"):
    return CandidateExtractionInput(
        work_item_id="WORK-1",
        requirements=[RequirementInput(requirement_id="REQ-1", text="Фото")],
        source_type="document",
        source_content=content,
        source_provenance=SourceProvenance(source_id="SRC-1", reference=reference),
    )


def candidate(**overrides):
    values = {
        "requirement_id": "REQ-1",
        "source_id": "SRC-1",
        "source_type": "document",
        "reference": "doc:42",
        "excerpt": "Фото оси А-12.",
        "interpretation": "Фрагмент может относиться к требованию; решение принимает человек.",
        "uncertainty": "found",
    }
    values.update(overrides)
    return values


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"requirement_id": "REQ-INVENTED"}, "requirement_id"),
        ({"source_id": "SRC-INVENTED"}, "source_id"),
        ({"source_type": "image"}, "source_type"),
        ({"reference": "page:12"}, "reference"),
        ({"excerpt": ""}, "excerpt"),
        ({"excerpt": "Перефразированный текст"}, "substring"),
    ],
)
def test_identity_reference_and_excerpt_protections(overrides, message):
    with pytest.raises(AIError) as captured:
        CandidateEvidenceExtractor(
            FakeProvider(response={"candidates": [candidate(**overrides)]})
        ).extract_candidates(make_input())
    assert captured.value.code == AIErrorCode.INVALID_OUTPUT
    assert message in str(captured.value)


def test_none_reference_is_allowed_and_supplied_reference_is_preserved():
    without_reference = CandidateEvidenceExtractor(
        FakeProvider(response={"candidates": [candidate(reference=None)]})
    ).extract_candidates(make_input())[0]
    preserved = CandidateEvidenceExtractor(
        FakeProvider(response={"candidates": [candidate()]})
    ).extract_candidates(make_input())[0]
    assert without_reference.reference is None
    assert preserved.reference == "doc:42"


@pytest.mark.parametrize(
    "content",
    [
        "Фото оси А-12, марка B25.",
        "А-12 осіндегі фото, B25 маркасы.",
        "Фото / сурет: ось А-12, B25, 250 мм.",
    ],
)
def test_ru_kz_and_mixed_excerpt_is_preserved_exactly(content):
    result = CandidateEvidenceExtractor(FakeProvider("valid_candidate")).extract_candidates(
        make_input(content=content)
    )
    assert result[0].excerpt == content
    assert "А-12" in result[0].excerpt
    assert "B25" in result[0].excerpt


def test_candidate_does_not_mutate_input_or_create_workflow_truth():
    extraction_input = make_input()
    before = extraction_input.model_dump()
    result = CandidateEvidenceExtractor(FakeProvider()).extract_candidates(extraction_input)
    assert extraction_input.model_dump() == before
    serialized = result[0].model_dump()
    assert "VALIDATED_EVIDENCE" not in serialized.values()
    assert "CONFIRMED" not in serialized.values()
    assert not ({"approved", "accepted", "workflow_status", "next_stage"} & serialized.keys())
