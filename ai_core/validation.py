from __future__ import annotations

import re

from .contracts import CandidateEvidenceBatch, CandidateExtractionInput
from .errors import AICandidateValidationError


_FORBIDDEN_STATUS_PATTERN = re.compile(
    r"\b(?:VALIDATED_EVIDENCE|CONFIRMED|CORRECTION_REQUIRED|"
    r"PACKET_READY(?:_FOR_INSPECTION)?|NEXT_STAGE_ALLOWED|UNLOCKED)\b",
    re.IGNORECASE,
)
_FORBIDDEN_DECISION_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\b(?:requirement|work|evidence|document|object|inspection|packet)\s+"
        r"(?:is|was|has been)\s+(?:satisfied|valid(?:ated)?|compliant|approved|accepted|passed|confirmed|ready)\b",
        r"\bnext stage\s+(?:is\s+)?(?:permitted|allowed|unlocked)\b",
        r"\b(?:требование выполнено|работа (?:принята|одобрена)|инспекция пройдена|"
        r"объект принят|пакет готов|следующий этап (?:разреш[её]н|открыт))\b",
        r"\b(?:талап орындалды|жұмыс қабылданды|инспекциядан өтті|нысан қабылданды|"
        r"пакет дайын|келесі кезеңге рұқсат берілді)\b",
    )
)


def validate_candidate_batch(
    batch: CandidateEvidenceBatch,
    extraction_input: CandidateExtractionInput,
) -> None:
    allowed_requirement_ids = {item.requirement_id for item in extraction_input.requirements}
    expected_source_id = extraction_input.source_provenance.source_id
    expected_source_type = extraction_input.source_type
    supplied_reference = extraction_input.source_provenance.reference

    for candidate in batch.candidates:
        if candidate.requirement_id not in allowed_requirement_ids:
            raise AICandidateValidationError("provider invented requirement_id")
        if candidate.source_id != expected_source_id:
            raise AICandidateValidationError("provider changed source_id")
        if candidate.source_type != expected_source_type:
            raise AICandidateValidationError("provider changed source_type")
        if not candidate.excerpt.strip():
            raise AICandidateValidationError("candidate excerpt is empty")
        if candidate.excerpt not in extraction_input.source_content:
            raise AICandidateValidationError("candidate excerpt is not a literal source substring")
        if candidate.reference is not None and candidate.reference != supplied_reference:
            raise AICandidateValidationError("provider invented source reference")
        if _FORBIDDEN_STATUS_PATTERN.search(candidate.interpretation):
            raise AICandidateValidationError("interpretation contains a workflow status")
        if any(pattern.search(candidate.interpretation) for pattern in _FORBIDDEN_DECISION_PATTERNS):
            raise AICandidateValidationError("interpretation assigns a business decision")
