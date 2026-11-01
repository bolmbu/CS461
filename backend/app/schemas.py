"""Validate model outputs independently from user input and UI rendering."""
from pydantic import BaseModel, ConfigDict, Field


class Output(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class CompanyFact(Output):
    text: str = Field(min_length=1, max_length=1200)
    source_id: int = Field(ge=0)


class CompanySummary(Output):
    facts: list[CompanyFact] = Field(max_length=8)
    missing_fields: list[str] = Field(max_length=10)


class Question(Output):
    question: str = Field(min_length=1, max_length=2000)
    evidence_quote: str = Field(max_length=10000)


class FAQAnswer(Output):
    answer: str = Field(min_length=1, max_length=6000)
    source_ids: list[str] = Field(max_length=3)
    abstained: bool


class Dimension(Output):
    dimension: str = Field(min_length=1, max_length=200)
    score: int = Field(ge=1, le=5)
    evidence: str = Field(min_length=1, max_length=10000)
    feedback: str = Field(min_length=1, max_length=3000)
    example_improvement: str = Field(max_length=3000)


class Report(Output):
    dimensions: list[Dimension] = Field(min_length=5, max_length=5)
    action_items: list[str] = Field(max_length=10)
