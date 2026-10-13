from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from .edges import route_after_router
from .nodes import (
    fanout,
    orchestrator_node,
    reducer_node,
    research_node,
    router_node,
    worker_node,
)
from .state import BlogState


def build_workflow():
    graph = StateGraph(BlogState)
    graph.add_node("router", router_node)
    graph.add_node("research", research_node)
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("worker", worker_node)
    graph.add_node("reducer", reducer_node)
    graph.add_edge(START, "router")
    graph.add_conditional_edges(
        "router",
        route_after_router,
        {"research": "research", "orchestrator": "orchestrator"},
    )
    graph.add_edge("research", "orchestrator")
    graph.add_conditional_edges(
        "orchestrator",
        lambda state: [Send("worker", payload) for payload in fanout(state)],
        ["worker"],
    )
    graph.add_edge("worker", "reducer")
    graph.add_edge("reducer", END)
    return graph.compile()


blog_writer = build_workflow()


def build_planning_workflow():
    graph = StateGraph(BlogState)
    graph.add_node("router", router_node)
    graph.add_node("research", research_node)
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_edge(START, "router")
    graph.add_conditional_edges(
        "router",
        route_after_router,
        {"research": "research", "orchestrator": "orchestrator"},
    )
    graph.add_edge("research", "orchestrator")
    graph.add_edge("orchestrator", END)
    return graph.compile()


def build_approved_workflow():
    graph = StateGraph(BlogState)
    graph.add_node("worker", worker_node)
    graph.add_node("reducer", reducer_node)
    graph.add_conditional_edges(
        START,
        lambda state: [Send("worker", payload) for payload in fanout(state)],
        ["worker"],
    )
    graph.add_edge("worker", "reducer")
    graph.add_edge("reducer", END)
    return graph.compile()


planning_writer = build_planning_workflow()
approved_writer = build_approved_workflow()
