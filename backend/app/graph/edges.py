from .state import BlogState


def route_after_feedback(state: BlogState) -> str:
    if state.feedback_action == "approve":
        return "router"
    if state.feedback_action == "revise":
        return "outline"
    return "__end__"


def route_at_start(state: BlogState) -> str:
    return "summarise" if state.supporting_context.strip() else "outline"
