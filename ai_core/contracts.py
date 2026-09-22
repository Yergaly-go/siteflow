from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _require_non_empty(value: str, field_name: str) -> str:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


class RequirementInput(StrictModel):
    requirement_id: str
    text: str

    @field_validator("requirement_id", "text")
    @classmethod
    def validate_non_empty(cls, value: str, info: Any) -> str:
        return _require_non_empty(value, info.field_name)


class SourceProvenance(StrictModel):
    source_id: str
    source_version: str | None = None
    filename: str | None = None
    reference: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("source_id")
    @classmethod
    def validate_source_id(cls, value: str) -> str:
        return _require_non_empty(value, "source_id")


class CandidateExtractionInput(StrictModel):
    work_item_id: str
    requirements: list[RequirementInput]
    source_type: str
    source_content: str
    source_provenance: SourceProvenance

    @field_validator("work_item_id", "source_type")
    @classmethod
    def validate_non_empty(cls, value: str, info: Any) -> str:
        return _require_non_empty(value, info.field_name)

    @model_validator(mode="after")
    def validate_unique_requirement_ids(self) -> "CandidateExtractionInput":
        requirement_ids = [item.requirement_id for item in self.requirements]
        if len(requirement_ids) != len(set(requirement_ids)):
            raise ValueError("requirement_id values must be unique")
        return self


class CandidateEvidence(StrictModel):
    requirement_id: str
    source_id: str
    source_type: str
    reference: str | None
    excerpt: str
    interpretation: str
    uncertainty: Literal["found", "ambiguous", "conflicting", "unsupported"]


class CandidateEvidenceBatch(StrictModel):
    candidates: list[CandidateEvidence]
