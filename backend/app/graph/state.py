from operator import add
from typing import Annotated, Literal, Optional, TypedDict

from pydantic import BaseModel, Field


class Task(BaseModel):
    id: int = Field(ge=1)
    title: str = Field(min_length=1)
    brief: str = Field(min_length=1, description="What this section must cover")


class Plan(BaseModel):
    blog_title: str = Field(min_length=1)
    tasks: list[Task] = Field(min_length=1)


class EvidenceItem(BaseModel):
    title: str = Field(min_length=1)
    url: str = Field(min_length=1)
    published_at: Optional[str] = None
    source: Optional[str] = None
    snippet: Optional[str] = None


class RouterDecision(BaseModel):
    needs_research: bool
    mode: Literal["closed_book", "hybrid", "open_book"]
    queries: list[str] = Field(default_factory=list)


class EvidencePack(BaseModel):
    evidence: list[EvidenceItem] = Field(default_factory=list)


class BlogState(TypedDict, total=False):
    topic: str
    supporting_context: str
    plan: Optional[Plan]
    mode: str
    needs_research: bool
    queries: list[str]
    evidence: list[EvidenceItem]
    sections: Annotated[list[tuple[int, str]], add]
    final: str