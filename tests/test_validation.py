import pytest
from pydantic import ValidationError

from ai_core.contracts import CandidateEvidence, CandidateExtractionInput, RequirementInput, SourceProvenance


@pytest.mark.parametrize("field", ["requirement_id", "text"])
def test_requirement_rejects_empty_identity_and_text(field):
    values = {"requirement_id": "REQ-1", "text": "Photo"}
    values[field] = "   "
    with pytest.raises(ValidationError):
        RequirementInput(**values)


@pytest.mark.parametrize("field", ["work_item_id", "source_type"])
def test_input_rejects_empty_core_identity(field):
    values = {
        "work_item_id": "WORK-1",
        "requirements": [],
        "source_type": "text/plain",
        "source_content": "",
        "source_provenance": SourceProvenance(source_id="SRC-1"),
    }
    values[field] = " "
    with pytest.raises(ValidationError):
        CandidateExtractionInput(**values)


def test_source_id_is_non_empty_and_metadata_is_not_shared():
    with pytest.raises(ValidationError):
        SourceProvenance(source_id="")
    first = SourceProvenance(source_id="SRC-1")
    second = SourceProvenance(source_id="SRC-2")
    first.metadata["key"] = "value"
    assert second.metadata == {}


def test_requirement_ids_must_be_unique():
    with pytest.raises(ValidationError):
        CandidateExtractionInput(
            work_item_id="WORK-1",
            requirements=[
                RequirementInput(requirement_id="REQ-1", text="First"),
                RequirementInput(requirement_id="REQ-1", text="Second"),
            ],
            source_type="text/plain",
            source_content="source",
            source_provenance=SourceProvenance(source_id="SRC-1"),
        )


@pytest.mark.parametrize("model", [RequirementInput, SourceProvenance, CandidateEvidence])
def test_ai_facing_models_forbid_extra_fields(model):
    values = {
        RequirementInput: {"requirement_id": "REQ-1", "text": "Photo"},
        SourceProvenance: {"source_id": "SRC-1"},
        CandidateEvidence: {
            "requirement_id": "REQ-1",
            "source_id": "SRC-1",
            "source_type": "text/plain",
            "reference": None,
            "excerpt": "Photo",
            "interpretation": "Potential match.",
            "uncertainty": "found",
        },
    }[model]
    with pytest.raises(ValidationError):
        model(**values, approved=True)


def test_candidate_rejects_invalid_uncertainty():
    with pytest.raises(ValidationError):
        CandidateEvidence(
            requirement_id="REQ-1",
            source_id="SRC-1",
            source_type="text/plain",
            reference=None,
            excerpt="Photo",
            interpretation="Potential match.",
            uncertainty="certain",
        )
