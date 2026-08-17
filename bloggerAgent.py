from typing import TypedDict,List,Annotated,Optional,Literal
from pydantic import BaseModel,Field
from langgraph.graph import StateGraph,START,END
from langgraph.types import Send
import operator
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage,HumanMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv
load_dotenv()
import re
from pathlib import Path


# llm=ChatOpenAI(base_url="http://127.0.0.1:8080",model='gemma4',api_key='not-required') llama cpp
llm=ChatOpenAI(base_url="http://localhost:11434/v1",model='gemma4',api_key='not-required')


#tavily search fn
tavily_tool = TavilySearchResults()

def _tavily_search(query: str, max_results: int = 6) -> List[dict]:
    """
    Executes a web search using LangChain's Tavily tool wrapper.
    Returns a list of dicts containing 'url' and 'content'.
    """
    try:
        # Pass configuration directly to the tool invocation
        return tavily_tool.invoke({"query": query}, config={"max_results": max_results})
    except Exception as e:
        print(f"Tavily search failed for query '{query}': {e}")
        return []
    

    

# ==========================================
# 1. Pydantic Schemas & State
# ==========================================
class Task(BaseModel):
    id: int
    title: str
    brief: str = Field(..., description='what to cover')

class Plan(BaseModel):
    blog_title: str
    tasks: List[Task]

class EvidenceItem(BaseModel):
    title: str
    url: str
    published_at: Optional[str] = None
    source: Optional[str] = None

class RouterDecision(BaseModel):
    needs_research: bool
    mode: Literal['closed_book', 'hybrid', 'open_book']
    queries: List[str] = Field(default_factory=list)

class EvidencePack(BaseModel):
    evidence: List[EvidenceItem] = Field(default_factory=list)


class State(TypedDict):
    topic: str
    plan: Optional[Plan]
    mode: str 
    needs_research: bool 
    queries: List[str]            
    evidence: List[EvidenceItem]
    sections: Annotated[List[tuple], operator.add] 
    final: str



ROUTER_SYSTEM="""
You are a routing module for a technical blog planner.

ROUTER_SYSTEM

Decide whether web research is needed BEFORE planning.

Modes:

- closed_book (needs_research = false):
  Evergreen topics where correctness does not depend on recent facts (concepts, fundamentals).

- hybrid (needs_research = true):
  Mostly evergreen topics that benefit from up-to-date examples, tools, models, benchmarks, or best practices.

- open_book (needs_research = true):
  Mostly time-sensitive or rapidly changing topics, such as:
  - "latest" news
  - "this week" or "last week" updates
  - rankings
  - pricing
  - product releases
  - policy or regulatory changes

If needs_research = true:
- Output 3–10 high-signal search queries.
- Queries should be specific and narrowly scoped.
- Avoid generic queries like "AI" or "LLM".
- If the user specifies a time constraint (e.g., "latest", "this week", or "last week"), reflect that constraint explicitly in every relevant search query.
"""

def router_node(state: State) -> dict:
    topic = state['topic']
    decider = llm.with_structured_output(RouterDecision)
    decision = decider.invoke([
        SystemMessage(content=ROUTER_SYSTEM),
        HumanMessage(content=f"Topic: {topic}")
    ])
    return {
        "needs_research": decision.needs_research,
        "mode": decision.mode,
        "queries": decision.queries,
    }

def route_next(state: State) -> str:
    return "research" if state['needs_research'] else "orchestrator"




RESEARCH_SYSTEM="""
You are a research synthesizer for technical writing.

SEARCH_SYSTEM

Given a set of search results, extract the most relevant information for the requested topic.

Guidelines:
- Only include items that have a URL.
- Prefer relevant and authoritative sources such as official company blogs, documentation, standards, research papers, and reputable publications.
- If a publication date is explicitly available in the search result, include it.
- If the publication date is missing or unclear, set it to `null`. Do not guess.
- Keep snippets concise and focused on the key information.
- Deduplicate results by URL.
- Preserve factual accuracy and do not add information that is not present in the source.

"""
def research_node(state: State) -> dict:
    queries = state.get("queries", []) or []
    max_results = 6
    raw_results: List[dict] = []

    for q in queries:
        raw_results.extend(_tavily_search(q, max_results=max_results))

    if not raw_results:
        return {'evidence': []}
    
    extractor = llm.with_structured_output(EvidencePack)
    pack = extractor.invoke([
        SystemMessage(content=RESEARCH_SYSTEM),
        HumanMessage(content=f"Raw results:\n{raw_results}")
    ])

    dedup = {}
    for e in pack.evidence:
        if e.url:
            dedup[e.url] = e
        
    return {"evidence": list(dedup.values())}


ORCH_SYSTEM=""" 
You are a senior technical writer and developer advocate.

PLANNER_SYSTEM

Your job is to produce a highly actionable outline for a technical blog post.

Hard requirements:
- Create 5–7 sections (tasks) suitable for the topic and audience.
- Each task must include:
  1. Goal (1 sentence)
  2. 3–6 concrete, specific, non-overlapping bullets
  3. Target word count (125–250)

Quality bar:
- Assume the reader is a developer; use correct technical terminology.
- Bullets must be actionable: build, compare, measure, verify, debug, optimize.
- Ensure the overall plan includes at least 2 of these:
  * minimal code sketch (for that section)
  * edge cases / failure modes
  * performance / cost considerations
  * security / privacy considerations (if relevant)
  * debugging / observability tips

Grounding rules:
- Mode `closed_book`:
  - Keep it evergreen; do not depend on evidence.
  - Set `requires_research=False` and `requires_citations=False`.

- Mode `hybrid`:
  - Use evidence for up-to-date examples (models, tools, releases, benchmarks).
  - Mark sections using fresh information as:
    - `requires_research=True`
    - `requires_citations=True`

- Mode `open_book`:
  - Set `blog_kind="news_roundup"`.
  - Every section should summarize recent events and their implications.
  - Do not include tutorial/how-to sections unless explicitly requested.
  - If evidence is empty or insufficient, create a plan that clearly states "insufficient sources" and include only what can be supported.

Output must strictly match the `Plan` schema.
"""

def orchestrator(state: State) -> dict:
    planner = llm.with_structured_output(Plan)
    evidence = state.get("evidence", [])
    mode = state.get('mode', 'closed_book')
    
    plan = planner.invoke([
        SystemMessage(content=ORCH_SYSTEM),
        HumanMessage(content=f"Topic: {state['topic']}\n"
                             f"Mode: {mode}\n\n"
                             f"Evidence:\n"
                             f"{[e.model_dump() for e in evidence][:16]}"),
    ])
    return {'plan': plan}



def fanout(state: State):
    return [
        Send(
            "worker",
            {
                "task": task.model_dump(),
                "topic": state["topic"],
                "plan": state["plan"].model_dump(),
                "mode": state['mode'],
                'evidence': [e.model_dump() for e in state.get('evidence', [])],
            },
        )
        for task in state["plan"].tasks
    ]




WORKER_SYSTEM=""" 
You are a senior technical writer and developer advocate.

Write ONE section of a technical blog post in Markdown.

Hard requirements:
- Follow the provided Goal.
- Cover ALL Bullets in order (do not skip or merge bullets).
- Stay close to the Target Word Count (±15%).
- Output ONLY the section content in Markdown (no blog title, no extra commentary).
- Start with a `## <Section Title>` heading.

Scope guard:
- If `blog_kind = "news_roundup"`:
  - Do not turn the section into a tutorial or how-to guide.
  - Do not explain web scraping, RSS, automation, or news collection unless explicitly requested.
  - Focus on summarizing events and explaining their implications.

Grounding policy:
- If `mode = "open_book"`:
  - Do not introduce any event, company, model, funding, benchmark, or policy claim unless it is supported by the provided Evidence.
  - For every factual claim from the Evidence, cite it as: `(Source)` where `Source` is a Markdown link to the provided URL.
  - Never invent citations.
  - If no supporting evidence exists, write: `Not found in provided sources.`

- If `requires_citations = true`:
  - Cite all outside-world factual claims using the provided Evidence URLs.
  - Evergreen technical explanations do not require citations unless they depend on recent information.

Code:
- If `requires_code = true`, include one minimal, correct code example relevant to the section.

Style:
- Use short paragraphs and bullet lists where appropriate.
- Use Markdown code fences for code.
- Be precise, implementation-oriented, and avoid marketing language or fluff.
"""

def worker(payload: dict) -> dict:
    task = Task(**payload["task"])
    topic = payload["topic"]
    plan = Plan(**payload["plan"])
    evidence = [EvidenceItem(**e) for e in payload.get("evidence", [])]
    mode = payload.get("mode", "closed_book")
    
    evidence_text = ""
    if evidence:
        evidence_text = "\n".join(
            f"- {e.title} | {e.url} | {(e.published_at or 'date:unknown').strip()}"
            for e in evidence[:20]
        )

    section_md = llm.invoke([
        SystemMessage(content=WORKER_SYSTEM),
        HumanMessage(content=(
            f"Blog title: {plan.blog_title}\n"
            f"Topic: {topic}\n"
            f"Mode: {mode}\n\n"
            f"Section title: {task.title}\n"
            f"Brief/Goal: {task.brief}\n\n"
            f"Evidence (ONLY use these URLs when citing):\n"
            f"{evidence_text}"
        )),
    ]).content.strip()

    return {"sections": [(task.id, section_md)]}


def reducer(state: State) -> dict:
    title = state['plan'].blog_title
    
 
    sorted_sections = sorted(state['sections'], key=lambda x: x[0])
    body = "\n\n".join([text for _, text in sorted_sections]).strip()
    
    final_md = f"# {title}\n\n{body}\n"

    safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
    filename = safe_title.lower().replace(" ", "_") + ".md"
    
    output_path = Path(filename)
    output_path.write_text(final_md, encoding='utf-8')
    print(f"Successfully saved to {filename}")
    
    return {'final': final_md}

# creating the graph and adding nodes and edges

graph = StateGraph(State)

graph.add_node("router", router_node)
graph.add_node("research", research_node)
graph.add_node("orchestrator", orchestrator)
graph.add_node("worker", worker)
graph.add_node("reducer", reducer)

graph.add_edge(START, "router")

graph.add_conditional_edges(
    "router",
    route_next,
    {
        "research": "research",
        "orchestrator": "orchestrator",
    },
)

graph.add_edge("research", "orchestrator")

graph.add_conditional_edges(
    "orchestrator",
    fanout,
    ["worker"],
)

graph.add_edge("worker", "reducer")
graph.add_edge("reducer", END)

app = graph.compile()

#  runner fn
def run(topic: str):
    out = app.invoke({
        "topic": topic,
        "mode": "closed_book",
        "needs_research": False,
        "queries": [],
        "evidence": [],
        "plan": None,
        "sections": []
    })
    return out


out=run('Blog Explaining the step-by-step mathematical derivation of the Backpropagation algorithm used in neural networks. Show all partial derivatives using LaTeX, explain the chain rule application at each layer, and describe how gradient descent uses these values to update weights and biases.')

print(out['final'])