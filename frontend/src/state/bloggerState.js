export const initialState = {
  currentView: "input",
  topic: "",
  files: null,
  instructions: "",
  logs: [],
  blogTitle: "",
  blogContent: "",
  error: "",
  proposal: null,
};

export function bloggerReducer(state, action) {
  switch (action.type) {
    case "topicChanged":
      return { ...state, topic: action.topic };
    case "filesChanged":
      return { ...state, files: action.files };
    case "instructionsChanged":
      return { ...state, instructions: action.instructions };
    case "planningStarted":
      return {
        ...state,
        currentView: "planning",
        topic: state.topic,
        instructions: "",
        logs: [],
        blogTitle: "",
        blogContent: "",
        error: "",
        proposal: null,
      };
    case "outlineReady":
      return {
        ...state,
        currentView: "approval",
        proposal: action.proposal,
        topic: action.proposal.topic,
        error: "",
      };
    case "generationStarted":
      return {
        ...state,
        currentView: "status",
        logs: action.logs,
        error: "",
      };
    case "workflowEvent": {
      const event = action.event;
      if (event.finished) {
        return {
          ...state,
          currentView: "results",
          blogContent: event.blog,
          blogTitle: event.blog_title,
        };
      }
      if (event.name === "start") return state;

      let matched = false;
      const logs = state.logs.map((log) => {
        if (log.id !== event.id) return log;

        matched = true;
        return {
          ...log,
          ...event,
          status: event.name === "worker" ? "ready" : log.status,
          message: event.name === "worker" ? "Ready" : event.message,
        };
      });

      return {
        ...state,
        logs: matched ? logs : [...logs, event],
      };
    }
    case "revisionStarted":
      return {
        ...state,
        currentView: "planning",
        instructions: "",
        error: "",
      };
    case "revisionFailed":
      return {
        ...state,
        currentView: "approval",
        error: action.error,
      };
    case "cancelFailed":
      return { ...state, error: action.error };
    case "generationFailed":
      return {
        ...state,
        currentView: "status",
        error: action.error,
      };
    case "planningFailed":
      return {
        ...state,
        currentView: "input",
        error: action.error,
      };
    case "returnToInput":
      return { ...state, currentView: "input", error: "" };
    case "cancelOutline":
      return { ...initialState, files: null };
    default:
      return state;
  }
}
