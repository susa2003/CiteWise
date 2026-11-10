from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.retrieval import SourceResult


class AnalysisRequest(BaseModel):
    document_id: str


class AnalysisFindingProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str
    text: str = Field(min_length=2, max_length=4000)
    chunk_ids: list[str] = Field(default_factory=list, max_length=8)


class AnalysisProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    findings: list[AnalysisFindingProposal] = Field(default_factory=list, max_length=20)


class AnalysisFinding(BaseModel):
    category: str
    text: str
    sources: list[SourceResult]


class AnalysisResponse(BaseModel):
    mode: str
    message: str | None = None
    run_id: str | None = None
    document_id: str
    findings: list[AnalysisFinding] = Field(default_factory=list)


class ComparisonRequest(BaseModel):
    document_ids: list[str] = Field(min_length=2, max_length=5)


class PaperFindingProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    text: str
    chunk_ids: list[str] = Field(default_factory=list, max_length=8)


class ComparisonCategoryProposal(BaseModel):
    category: str
    paper_findings: list[PaperFindingProposal]


class ComparisonPointProposal(BaseModel):
    text: str
    chunk_ids: list[str] = Field(default_factory=list, max_length=8)


class PerformancePaperContextProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    metric: str
    dataset: str
    conditions: str
    chunk_ids: list[str] = Field(min_length=1, max_length=8)


class PerformanceComparisonProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comparable: bool
    text: str
    papers: list[PerformancePaperContextProposal] = Field(default_factory=list, max_length=5)


class ComparisonProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    categories: list[ComparisonCategoryProposal] = Field(default_factory=list)
    similarities: list[ComparisonPointProposal] = Field(default_factory=list)
    differences: list[ComparisonPointProposal] = Field(default_factory=list)
    methodological_strengths: list[ComparisonPointProposal] = Field(default_factory=list)
    methodological_weaknesses: list[ComparisonPointProposal] = Field(default_factory=list)
    dataset_differences: list[ComparisonPointProposal] = Field(default_factory=list)
    research_opportunities: list[ComparisonPointProposal] = Field(default_factory=list)
    performance_comparison: PerformanceComparisonProposal | None = None


class PaperFinding(BaseModel):
    document_id: str
    filename: str
    text: str
    sources: list[SourceResult]


class ComparisonCategory(BaseModel):
    category: str
    papers: list[PaperFinding]


class ComparisonPoint(BaseModel):
    text: str
    sources: list[SourceResult]


class PerformanceComparison(BaseModel):
    comparable: bool
    text: str
    metric: str | None = None
    dataset: str | None = None
    conditions: str | None = None
    sources: list[SourceResult] = Field(default_factory=list)


class ComparisonResponse(BaseModel):
    mode: str
    message: str | None = None
    run_id: str | None = None
    document_ids: list[str]
    categories: list[ComparisonCategory] = Field(default_factory=list)
    similarities: list[ComparisonPoint] = Field(default_factory=list)
    differences: list[ComparisonPoint] = Field(default_factory=list)
    methodological_strengths: list[ComparisonPoint] = Field(default_factory=list)
    methodological_weaknesses: list[ComparisonPoint] = Field(default_factory=list)
    dataset_differences: list[ComparisonPoint] = Field(default_factory=list)
    research_opportunities: list[ComparisonPoint] = Field(default_factory=list)
    performance_comparison: PerformanceComparison | None = None


class GapRequest(BaseModel):
    document_ids: list[str] = Field(min_length=1, max_length=20)


GapKind = Literal["explicit_limitation", "inferred_opportunity", "hypothesis"]


class GapProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    explanation: str
    kind: GapKind
    chunk_ids: list[str] = Field(min_length=1, max_length=8)
    why_it_matters: str
    possible_direction: str
    suggested_experiments: list[str] = Field(default_factory=list)
    potential_metrics: list[str] = Field(default_factory=list)


class GapProposalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gaps: list[GapProposal] = Field(default_factory=list, max_length=20)


class GapFinding(BaseModel):
    title: str
    explanation: str
    kind: GapKind
    sources: list[SourceResult]
    why_it_matters: str
    possible_direction: str
    suggested_experiments: list[str]
    potential_metrics: list[str]


class GapResponse(BaseModel):
    mode: str
    message: str | None = None
    run_id: str | None = None
    document_ids: list[str]
    gaps: list[GapFinding] = Field(default_factory=list)


SummaryFormat = Literal["short", "detailed_technical", "beginner_friendly", "academic", "methodology_focused", "results_focused"]


class SummaryRequest(BaseModel):
    document_id: str
    format: SummaryFormat


class SummarySectionProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    heading: str
    text: str
    interpretation: bool = False
    chunk_ids: list[str] = Field(min_length=1, max_length=8)


class SummaryProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sections: list[SummarySectionProposal] = Field(default_factory=list, max_length=20)


class SummarySection(BaseModel):
    heading: str
    text: str
    interpretation: bool
    sources: list[SourceResult]


class SummaryResponse(BaseModel):
    mode: str
    message: str | None = None
    run_id: str | None = None
    document_id: str
    format: SummaryFormat
    sections: list[SummarySection] = Field(default_factory=list)
