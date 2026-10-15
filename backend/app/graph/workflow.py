from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from .edges import route_after_feedback, route_at_start
from .nodes import (
    document_summary_generator_node,
    fanout,
    human_feedback_node,
    outline_generator_node,
    reducer_node,
    research_node,
    router_node,
    worker_node,
)
from .state import BlogState


def dispatch_workers(state: BlogState) -> list[Send]:
    return [Send("worker", payload) for payload in fanout(state)]


def build_workflow():
    graph = StateGraph(BlogState)
    graph.add_node("summarise", document_summary_generator_node)
    graph.add_node("outline", outline_generator_node)
    graph.add_node("human_feedback", human_feedback_node)
    graph.add_node("router", router_node)
    graph.add_node("research", research_node)
    graph.add_node("worker", worker_node)
    graph.add_node("reducer", reducer_node)

    graph.add_conditional_edges(
        START,
        route_at_start,
        {"summarise": "summarise", "outline": "outline"},
    )
    graph.add_edge("summarise", "outline")
    graph.add_edge("outline", "human_feedback")
    graph.add_conditional_edges(
        "human_feedback",
        route_after_feedback,
        {"router": "router", "outline": "outline", END: END},
    )
    graph.add_edge("router", "research")
    graph.add_conditional_edges("research", dispatch_workers, ["worker"])
    graph.add_edge("worker", "reducer")
    graph.add_edge("reducer", END)

    return graph.compile(checkpointer=InMemorySaver())


blog_writer = build_workflow()
