from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from .base import ProviderFailureError, ProviderTimeoutError, ProviderUnavailableError


class FakeProvider:
    """Deterministic test provider. It never performs a network call."""

    def __init__(self, mode: str = "valid_candidate", *, response: Any = None) -> None:
        self.mode = mode
        self.response = response
        self.last_task: str | None = None
        self.last_input_data: dict | None = None

    def generate_structured(
        self,
        *,
        task: str,
        input_data: dict,
        output_schema: type[BaseModel],
    ) -> BaseModel:
        self.last_task = task
        self.last_input_data = input_data

        if self.mode == "timeout":
            raise ProviderTimeoutError("fake provider timeout")
        if self.mode in {"unavailable", "provider_unavailable"}:
            raise ProviderUnavailableError("fake provider unavailable")
        if self.mode in {"failure", "provider_failure"}:
            raise ProviderFailureError("fake provider failure")
        if self.mode == "invalid_output":
            return {"unexpected": True}  # type: ignore[return-value]
        if self.response is not None:
            if isinstance(self.response, BaseModel):
                return self.response
            return output_schema.model_validate(self.response)

        if self.mode in {"zero", "zero_candidates"}:
            return output_schema.model_validate({"candidates": []})

        uncertainty = {
            "ambiguous_candidate": "ambiguous",
            "conflicting_candidate": "conflicting",
            "unsupported_candidate": "unsupported",
        }.get(self.mode, "found")
        requirement_ids = [item["requirement_id"] for item in input_data["requirements"]]
        if self.mode in {"multiple", "multiple_candidates"} and requirement_ids:
            selected_ids = requirement_ids
        else:
            selected_ids = requirement_ids[:1]
        source_content = input_data["source_content"]
        candidates = [
            {
                "requirement_id": requirement_id,
                "source_id": input_data["source_provenance"]["source_id"],
                "source_type": input_data["source_type"],
                "reference": input_data["source_provenance"].get("reference"),
                "excerpt": source_content,
                "interpretation": "Potentially relevant source excerpt for human review.",
                "uncertainty": uncertainty,
            }
            for requirement_id in selected_ids
        ]
        return output_schema.model_validate({"candidates": candidates})
