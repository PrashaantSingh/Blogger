import os
from typing import Any

from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from .state import BlogState, EvidenceItem, EvidencePack, Plan, RouterDecision, Task

load_dotenv()


def _model() -> ChatOpenAI:
    return ChatOpenAI(
        base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
        model=os.getenv("LLM_MODEL", "gemma"),
        api_key=os.getenv("OPENAI_API_KEY", "not-required"),
        temperature=0.2,
    )


ROUTER_SYSTEM = """You route blog requests before planning.
Use closed_book for evergreen concepts and fundamentals.
Use hybrid when current tools, examples, benchmarks, or best practices improve the article.
Use open_book for latest news, pricing, rankings, releases, policy, or other time-sensitive topics.
For research modes return 3-6 specific queries. For closed_book return an empty query list.
"""


def router_node(state: BlogState) -> dict[str, Any]:
    decision = _model().with_structured_output(RouterDecision).invoke(
        [SystemMessage(content=ROUTER_SYSTEM), HumanMessage(content=state["topic"])]
    )
    if not decision.needs_research:
        decision.queries = []
        decision.mode = "closed_book"
    return decision.model_dump()


def research_node(state: BlogState) -> dict[str, Any]:
    if not state.get("needs_research") or not state.get("queries"):
        return {"evidence": []}

    search = TavilySearchResults(
        max_results=int(os.getenv("TAVILY_MAX_RESULTS", "5")),
        search_depth="advanced",
    )
    raw_results: list[dict[str, Any]] = []
    for query in state["queries"]:
        results = search.invoke({"query": query})
        if isinstance(results, list):
            raw_results.extend(item for item in results if isinstance(item, dict))

    if not raw_results:
        return {"evidence": []}

    pack = _model().with_structured_output(EvidencePack).invoke(
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
    deduplicated: dict[str, EvidenceItem] = {}
    for item in pack.evidence:
        deduplicated[item.url] = item
    return {"evidence": list(deduplicated.values())}


PLANNER_SYSTEM = """You are an expert editor. Create an accurate, engaging plan for a blog
in any field: science, history, education, culture, business, health, technology, or any
other subject the reader requests. Match the depth, vocabulary, tone, and structure to the
topic and audience. Do not force programming, developer, software, or optimization framing
unless the topic explicitly asks for it.
Return 5-7 non-overlapping sections. Each brief must include a goal and concrete points.
Include examples, evidence, context, practical guidance, comparisons, or limitations only
when they naturally fit the subject.
For open_book topics, make every section about recent events and implications; never invent
facts when evidence is insufficient. Return only the requested schema.
"""


def orchestrator_node(state: BlogState) -> dict[str, Any]:
    evidence = [item.model_dump() for item in state.get("evidence", [])]
    plan = _model().with_structured_output(Plan).invoke(
        [
            SystemMessage(content=PLANNER_SYSTEM),
            HumanMessage(
                content=(
                    f"Topic: {state['topic']}\nMode: {state.get('mode', 'closed_book')}\n"
                    f"Supporting document:\n{state.get('supporting_context', '')[:30000]}\n"
                    f"Evidence:\n{evidence[:20]}"
                )
            ),
        ]
    )
    return {"plan": plan}


def fanout(state: BlogState) -> list[dict[str, Any]]:
    plan = state["plan"]
    if plan is None:
        raise ValueError("Planner returned no plan")
    return [
        {
            "task": task.model_dump(),
            "topic": state["topic"],
            "mode": state.get("mode", "closed_book"),
            "evidence": [item.model_dump() for item in state.get("evidence", [])],
            "blog_title": plan.blog_title,
            "supporting_context": state.get("supporting_context", ""),
        }
        for task in plan.tasks
    ]


WORKER_SYSTEM = """Write one publication-ready Markdown section for the requested subject.
Respect the subject's domain and intended audience. Explain foundational concepts clearly
when the topic is educational, and do not reinterpret a science, history, culture, or
general-interest topic as a software or engineering problem.
Start with exactly one `##` heading, cover every point in the brief, and do not add commentary
outside the section. Use only the supplied evidence for time-sensitive factual claims. For
open_book requests, cite supported claims as Markdown links and write "Not found in provided
sources." when evidence does not support a claim. Never invent URLs.
"""


def worker_node(payload: dict[str, Any]) -> dict[str, Any]:
    task = Task.model_validate(payload["task"])
    evidence = payload.get("evidence", [])
    response = _model().invoke(
        [
            SystemMessage(content=WORKER_SYSTEM),
            HumanMessage(
                content=(
                    f"Blog title: {payload['blog_title']}\nTopic: {payload['topic']}\n"
                    f"Mode: {payload['mode']}\nSection: {task.title}\nBrief: {task.brief}\n"
                    f"Supporting document:\n{payload.get('supporting_context', '')[:30000]}\n"
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
    plan = state.get("plan")
    if plan is None:
        raise ValueError("Cannot reduce a missing plan")
    sections = sorted(state.get("sections", []), key=lambda section: section[0])
    if len(sections) != len(plan.tasks):
        raise ValueError("Cannot reduce incomplete section output")
    body = "\n\n".join(content for _, content in sections)
    return {"final": f"# {plan.blog_title}\n\n{body}\n"}
