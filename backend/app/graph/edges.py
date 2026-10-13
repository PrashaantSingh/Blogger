from .state import BlogState


def route_after_router(state: BlogState) -> str:
    return "research" if state.get("needs_research") else "orchestrator"