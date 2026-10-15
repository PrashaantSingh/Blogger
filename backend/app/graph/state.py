from operator import add
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class Task(BaseModel):
    id: int = Field(ge=1)
    title: str = Field(min_length=1)
    brief: str = Field(
        min_length=1,
        description="A brief description of what this section must cover.",
    )


class Plan(BaseModel):
    blog_title: str = Field(description="A suitable title for the blog.")
    tasks: list[Task] = Field(
        min_length=1,
        description="Ordered sections of the blog.",
    )
    queries: list[str] = Field(
        default_factory=list,
        description="Specific search queries needed to gather missing information.",
    )
    needs_research: bool = Field(
        description="Whether external internet research is necessary for this blog.",
    )
    is_document_relevant: bool = Field(
        description=(
            "Whether the uploaded document summary contains useful information "
            "relevant to the blog topic."
        ),
    )


class EvidenceItem(BaseModel):
    title: str = Field(min_length=1)
    url: str = Field(min_length=1)
    published_at: str | None = None
    source: str | None = None
    snippet: str | None = None


class RouterDecision(BaseModel):
    needs_research: bool
    mode: Literal["closed_book", "hybrid", "open_book"]
    queries: list[str] = Field(default_factory=list)


class EvidencePack(BaseModel):
    evidence: list[EvidenceItem] = Field(default_factory=list)


class BlogState(BaseModel):
    topic: str
    supporting_context: str
    document_batch_id: str
    document_summary: str
    plan: Plan | None = None
    mode: str
    feedback_action: str
    revision_instructions: str

    needs_research: bool
    is_document_relevant: bool
    queries: list[str]

    evidence: list[EvidenceItem]
    sections: Annotated[list[tuple[int, str]], add]
    final: str
