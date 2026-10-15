import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.types import interrupt
from pydantic import BaseModel, Field

from app.services.rag_service import retrieve_context

from .state import BlogState, EvidenceItem, EvidencePack, Plan, RouterDecision, Task

load_dotenv()


def _model() -> ChatOpenAI:
    return ChatOpenAI(
        base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
        model=os.getenv("LLM_MODEL", "gemma"),
        api_key=os.getenv("OPENAI_API_KEY", "not-required"),
        temperature=0.2,
    )


async def document_summary_generator_node(state: BlogState) -> dict[str, str]:
    if not state.supporting_context.strip():
        return {"document_summary": ""}

    response = await _model().ainvoke(
        f"""
You are a document summarizer.

Blog topic: {state.topic}

Supporting context:
{state.supporting_context}

Write a short, concise summary containing only information relevant
to the blog topic. Preserve the key topics and useful facts while
avoiding unnecessary details.

If the supporting context contains no useful information relevant
to the blog topic, return an empty string.

Return only the summary, without headings, explanations, or commentary.
"""
    )

    return {"document_summary": response.content.strip()}



outline_generator_template = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an expert blog outline generator.

BLOG TOPIC:
{blog_topic}

DOCUMENT SUMMARY:
{supporting_docs_summary}

PREVIOUS OUTLINE:
{previous_outline}

REVISION INSTRUCTIONS:
{revision_instructions}

If a previous outline is provided and there are no revision instructions,
create a meaningfully different alternative while keeping the same topic
and relevant document facts. This path is used when the user requests a
regeneration without specific changes.

1. DOCUMENT RELEVANCE
- Determine whether the document summary contains useful information
  relevant to the blog topic.
- Set is_document_relevant to false if the summary is empty or irrelevant.
- If irrelevant, ignore the document when generating the outline.
- If relevant, incorporate its useful information into the outline.

2. INTERNET RESEARCH
- Decide whether external internet research is needed.
- Set needs_research accordingly.
- If research is needed, generate specific search queries.
- Otherwise, return an empty queries list.

3. BLOG OUTLINE
- Generate a suitable blog title.
- Create logically ordered, non-redundant sections.
- Assign unique, sequential section IDs starting from 1.
- Give each section a clear brief describing what it should cover.

Return output matching the Plan schema.
"""
    )
])


class PlanRevision(BaseModel):
    """Only the plan fields and sections that a revision should change."""

    blog_title: str | None = Field(
        default=None,
        description="Set only when the requested revision changes the title.",
    )
    tasks: list[Task] = Field(
        default_factory=list,
        description=(
            "Only the sections that should change. Keep their existing IDs; "
            "omit all unaffected sections."
        ),
    )
    queries: list[str] | None = Field(default=None)
    needs_research: bool | None = Field(default=None)
    is_document_relevant: bool | None = Field(default=None)


revision_template = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You revise an existing blog outline according to the user's instructions.
Return a patch, not a replacement outline.

CURRENT OUTLINE:
{previous_outline}

BLOG TOPIC:
{blog_topic}

RELEVANT DOCUMENT SUMMARY:
{supporting_docs_summary}

USER REVISION INSTRUCTIONS:
{revision_instructions}

Return only fields that the user asked to change. For tasks, return only
the affected sections and keep their existing IDs. Preserve every omitted
section exactly as it appears in the current outline, including its order,
title, and brief. If the user names a numbered point or section, change
only that section unless the instruction explicitly asks for broader edits.
Interpret "first point" and "second point" as task IDs 1 and 2.
Do not change the title, research queries, research decision, or document
relevance unless the instructions require it. If the instructions request
a broad change that affects multiple sections, return all and only those
affected sections. Match the PlanRevision schema.
""",
    )
])


async def outline_generator_node(state: BlogState) -> dict:
    if state.plan is not None and state.revision_instructions.strip():
        revision_chain = revision_template | _model().with_structured_output(
            PlanRevision
        )
        revision = await revision_chain.ainvoke({
            "blog_topic": state.topic,
            "supporting_docs_summary": state.document_summary,
            "previous_outline": state.plan.model_dump_json(),
            "revision_instructions": state.revision_instructions,
        })

        revised_tasks = {task.id: task for task in revision.tasks}
        plan = Plan(
            blog_title=revision.blog_title or state.plan.blog_title,
            tasks=[
                revised_tasks.get(task.id, task)
                for task in state.plan.tasks
            ],
            queries=(
                revision.queries
                if revision.queries is not None
                else state.plan.queries
            ),
            needs_research=(
                revision.needs_research
                if revision.needs_research is not None
                else state.plan.needs_research
            ),
            is_document_relevant=(
                revision.is_document_relevant
                if revision.is_document_relevant is not None
                else state.plan.is_document_relevant
            ),
        )
    else:
        chain = outline_generator_template | _model().with_structured_output(Plan)
        plan = await chain.ainvoke({
            "blog_topic": state.topic,
            "supporting_docs_summary": state.document_summary,
            "previous_outline": (
                state.plan.model_dump() if state.plan is not None else "None"
            ),
            "revision_instructions": state.revision_instructions or "None",
        })

    return {
        "plan": plan,
        "is_document_relevant": plan.is_document_relevant,
        "needs_research": plan.needs_research,
        "queries": plan.queries,
    }



def human_feedback_node(state: BlogState) -> dict[str, str]:
    decision = interrupt(
        {
            "outline": state.plan,
            "message": "Do you approve this outline?",
        }
    )

    action = decision.get("action", "revise")
    return {
        "feedback_action": action,
        "revision_instructions": decision.get("instructions", ""),
    }


ROUTER_SYSTEM = """You route blog requests before planning.
Use closed_book for evergreen concepts and fundamentals.
Use hybrid when current tools, examples, benchmarks, or best practices improve the article.
Use open_book for latest news, pricing, rankings, releases, policy, or other time-sensitive topics.
For research modes return 3-6 specific queries. For closed_book return an empty query list.
"""


async def router_node(state: BlogState) -> dict[str, Any]:
    decision = await _model().with_structured_output(RouterDecision).ainvoke(
        [
            SystemMessage(content=ROUTER_SYSTEM),
            HumanMessage(
                content=(
                    f"Blog topic: {state.topic}\n"
                    f"Outline research decision: "
                    f"{state.plan.needs_research if state.plan else False}\n"
                    f"Outline research queries: "
                    f"{state.plan.queries if state.plan else []}"
                )
            ),
        ]
    )

    outline_needs_research = bool(state.plan and state.plan.needs_research)
    needs_research = decision.needs_research or outline_needs_research
    if not needs_research:
        return {
            "needs_research": False,
            "queries": [],
            "mode": "closed_book",
        }

    outline_queries = state.plan.queries if state.plan else []
    queries = (
        outline_queries
        if outline_needs_research and outline_queries
        else decision.queries
    )
    if not queries:
        queries = [state.topic]

    mode = decision.mode if decision.mode != "closed_book" else "hybrid"
    decision.needs_research = True
    decision.queries = queries
    decision.mode = mode
    return decision.model_dump()


async def research_node(state: BlogState) -> dict[str, Any]:
    if not state.needs_research or not state.queries:
        return {"evidence": []}

    search = TavilySearch(
        max_results=int(os.getenv("TAVILY_MAX_RESULTS", "5")),
        search_depth="advanced",
    )
    raw_results: list[dict[str, Any]] = []
    for query in state.queries:
        response = await search.ainvoke({"query": query})
        results = response.get("results", []) if isinstance(response, dict) else []
        if isinstance(results, list):
            raw_results.extend(item for item in results if isinstance(item, dict))

    if not raw_results:
        return {"evidence": []}

    pack = await _model().with_structured_output(EvidencePack).ainvoke(
        [
            SystemMessage(
                content=(
                    "Extract only relevant, authoritative sources from these search results. "
                    "Keep the original URL, do not invent dates or facts, deduplicate URLs, "
                    "and return an empty list when a result has no usable URL."
                )
            ),
            HumanMessage(content=str(raw_results)),
        ]
    )
    deduplicated = {item.url: item for item in pack.evidence}
    return {"evidence": list(deduplicated.values())}


def fanout(state: BlogState) -> list[dict[str, Any]]:
    plan = state.plan
    if plan is None:
        raise ValueError("Planner returned no plan")
    return [
        {
            "task": task.model_dump(),
            "topic": state.topic,
            "mode": state.mode,
            "evidence": [item.model_dump() for item in state.evidence],
            "blog_title": plan.blog_title,
            "document_summary": state.document_summary,
            "document_batch_id": state.document_batch_id,
            "supporting_context": state.supporting_context,
        }
        for task in plan.tasks
    ]


WORKER_SYSTEM = """Write one publication-ready Markdown section for the requested subject.
Respect the subject's domain and intended audience. Explain foundational concepts clearly
when the topic is educational, and do not reinterpret a science, history, culture, or
general-interest topic as a software or engineering problem.
Start with exactly one `##` heading, cover every point in the brief, and do not add commentary
outside the section. The document summary only signals what information may be available; never
use it as a source for article details. Use only supplied document excerpts for document-based
claims, preserve their meaning, and omit details the excerpts do not support. Use only supplied
web evidence for time-sensitive factual claims. Do not include citations, source titles,
bracketed references, Markdown links, or a references list in the article. If the supplied
evidence does not support a time-sensitive claim, omit that claim rather than adding a source
note. Never invent URLs.
"""


async def worker_node(payload: dict[str, Any]) -> dict[str, Any]:
    task = Task.model_validate(payload["task"])
    evidence = payload.get("evidence", [])
    supporting_context = payload.get("supporting_context", "")
    batch_id = payload.get("document_batch_id", "")
    if batch_id:
        section_query = (
            f"{payload['topic']}\n{task.title}\n{task.brief}\n"
            f"Document search guide: {payload.get('document_summary', '')[:2000]}"
        )
        supporting_context = (
            retrieve_context(section_query, batch_id) or supporting_context
        )

    response = await _model().ainvoke(
        [
            SystemMessage(content=WORKER_SYSTEM),
            HumanMessage(
                content=(
                    f"Blog title: {payload['blog_title']}\nTopic: {payload['topic']}\n"
                    f"Mode: {payload['mode']}\nSection: {task.title}\nBrief: {task.brief}\n"
                    "Document search guide (awareness only, not a source for factual detail):\n"
                    f"{payload.get('document_summary', '')[:10000]}\n"
                    f"Relevant supporting document excerpts:\n{supporting_context[:30000]}\n"
                    f"Evidence: {evidence[:20]}"
                )
            ),
        ]
    )
    content = response.content.strip()
    if not content:
        raise ValueError(f"Worker returned empty content for section {task.id}")
    return {"sections": [(task.id, content)]}


def reducer_node(state: BlogState) -> dict[str, str]:
    plan = state.plan
    if plan is None:
        raise ValueError("Cannot reduce a missing plan")
    sections = sorted(state.sections, key=lambda section: section[0])
    if len(sections) != len(plan.tasks):
        raise ValueError("Cannot reduce incomplete section output")
    body = "\n\n".join(content for _, content in sections)
    return {"final": f"# {plan.blog_title}\n\n{body}\n"}
