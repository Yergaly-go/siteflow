"""Offline, candidate-only AI foundation for SiteFlow."""

from .contracts import CandidateEvidence, CandidateExtractionInput, RequirementInput, SourceProvenance
from .extractor import CandidateEvidenceExtractor

__all__ = [
    "CandidateEvidence",
    "CandidateEvidenceExtractor",
    "CandidateExtractionInput",
    "RequirementInput",
    "SourceProvenance",
]
