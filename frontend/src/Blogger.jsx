import { useReducer, useRef } from "react";

import InputPage from "./components/InputPage";
import StatusPage from "./components/Logs";
import ResultsPage from "./components/ResultBlog";
import PlanApproval from "./components/PlanApproval";
import OutlineLoadingPage from "./components/OutlineLoadingPage";
import { bloggerReducer, initialState } from "./state/bloggerState";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function getResponseError(response, fallback) {
  const body = await response.json().catch(() => ({}));
  const detail =
    typeof body.detail === "string"
      ? body.detail
      : Array.isArray(body.detail)
        ? body.detail.map((item) => item.msg).join(", ")
        : "";

  return new Error(detail || `${fallback} (${response.status})`);
}

export default function Blogger() {
  const [state, dispatch] = useReducer(bloggerReducer, initialState);
  const requestIdRef = useRef(null);
  const activeControllerRef = useRef(null);
  const cancelRequestedRef = useRef(false);

  const handleEvent = (event) => {
    if (event.error) {
      throw new Error(event.detail || event.error);
    }
    dispatch({ type: "workflowEvent", event });
  };

  const handleStartGeneration = async (selectedTopic, supportingDocuments) => {
    dispatch({ type: "planningStarted" });
    const requestId = crypto.randomUUID();
    requestIdRef.current = requestId;
    cancelRequestedRef.current = false;
    const controller = new AbortController();
    activeControllerRef.current = controller;

    try {
      const formData = new FormData();
      formData.append("request_id", requestId);
      formData.append("topic", selectedTopic);

      if (supportingDocuments?.length) {
        supportingDocuments.forEach((file) => {
          formData.append("supporting_documents", file);
        });
      }

      const response = await fetch(`${API_URL}/generate`, {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });
      if (!response.ok)
        throw await getResponseError(response, "Planning request failed");

      dispatch({ type: "outlineReady", proposal: await response.json() });
    } catch (planningError) {
      if (cancelRequestedRef.current) return;
      dispatch({
        type: "planningFailed",
        error:
          planningError instanceof Error
            ? planningError.message
            : "Unable to create a blog plan.",
      });
    }
  };

  const handleApprove = async () => {
    const proposal = state.proposal;
    cancelRequestedRef.current = false;
    const controller = new AbortController();
    activeControllerRef.current = controller;
    dispatch({
      type: "generationStarted",
      logs: proposal.sections.map((section) => ({
        id: `section-${section.id}`,
        section: section.title,
        sectionId: section.id,
        name: "section",
        message: "Writing",
        status: "writing",
      })),
    });

    try {
      const response = await fetch(
        `${API_URL}/generate?approval_id=${encodeURIComponent(proposal.approval_id)}`,
        { signal: controller.signal },
      );
      if (!response.ok)
        throw await getResponseError(response, "Generation request failed");
      if (!response.body) throw new Error("Readable stream is not supported");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let generationComplete = false;

      const processLine = (line) => {
        if (!line.trim()) return;
        try {
          const event = JSON.parse(line);
          handleEvent(event);
          generationComplete ||= Boolean(event.finished);
        } catch (eventError) {
          if (eventError instanceof SyntaxError) {
            throw new Error("The server returned an invalid generation update.");
          }
          throw eventError;
        }
      };

      while (true) {
        const { value, done } = await reader.read();
        buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        lines.forEach(processLine);
        if (done) break;
      }
      processLine(buffer);
      if (!generationComplete) {
        throw new Error("Generation ended before the blog was complete.");
      }
    } catch (generationError) {
      if (cancelRequestedRef.current) return;
      console.error("Streaming error:", generationError);
      dispatch({
        type: "generationFailed",
        error:
          generationError instanceof Error
            ? generationError.message
            : "Unable to generate the blog.",
      });
    }
  };

  const handleRegenerateOutline = async (instructions) => {
    dispatch({ type: "revisionStarted" });
    cancelRequestedRef.current = false;
    const controller = new AbortController();
    activeControllerRef.current = controller;

    try {
      const response = await fetch(
        `${API_URL}/generate/${encodeURIComponent(state.proposal.approval_id)}/revise`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ instructions }),
          signal: controller.signal,
        },
      );
      if (!response.ok)
        throw await getResponseError(response, "Outline revision failed");

      dispatch({ type: "outlineReady", proposal: await response.json() });
    } catch (revisionError) {
      if (cancelRequestedRef.current) return;
      dispatch({
        type: "revisionFailed",
        error:
          revisionError instanceof Error
            ? revisionError.message
            : "Unable to regenerate the outline.",
      });
    }
  };

  const handleCancelGeneration = async () => {
    const requestId = state.proposal?.approval_id || requestIdRef.current;
    if (!requestId) {
      dispatch({ type: "cancelOutline" });
      return;
    }

    cancelRequestedRef.current = true;
    activeControllerRef.current?.abort();
    activeControllerRef.current = null;
    try {
      const response = await fetch(
        `${API_URL}/generate/${encodeURIComponent(requestId)}/cancel`,
        { method: "POST" },
      );
      if (!response.ok && response.status !== 410)
        throw await getResponseError(response, "Could not cancel this outline");

      requestIdRef.current = null;
      dispatch({ type: "cancelOutline" });
    } catch (cancelError) {
      cancelRequestedRef.current = false;
      dispatch({
        type: "cancelFailed",
        error:
          cancelError instanceof Error
            ? cancelError.message
            : "Could not cancel this outline.",
      });
    }
  };

  if (state.currentView === "planning") {
    return (
      <OutlineLoadingPage
        onCancel={handleCancelGeneration}
        error={state.error}
      />
    );
  }

  if (state.currentView === "approval") {
    return (
      <PlanApproval
        proposal={state.proposal}
        instructions={state.instructions}
        onInstructionsChange={(instructions) =>
          dispatch({ type: "instructionsChanged", instructions })
        }
        onApprove={handleApprove}
        onRegenerate={handleRegenerateOutline}
        onCancel={handleCancelGeneration}
        error={state.error}
      />
    );
  }

  if (state.currentView === "status") {
    return (
      <StatusPage
        logs={state.logs}
        sections={state.proposal?.sections || []}
        title={state.proposal?.blog_title}
        error={state.error}
        onCancel={handleCancelGeneration}
        onStartOver={() => dispatch({ type: "returnToInput" })}
      />
    );
  }

  if (state.currentView === "results") {
    return (
      <ResultsPage
        blogTitle={state.blogTitle}
        blogContent={state.blogContent}
        onReset={() => dispatch({ type: "returnToInput" })}
      />
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-8 p-6">
      <InputPage
        topic={state.topic}
        files={state.files}
        onTopicChange={(topic) => dispatch({ type: "topicChanged", topic })}
        onFilesChange={(files) => dispatch({ type: "filesChanged", files })}
        onSubmit={handleStartGeneration}
      />
      {state.error && (
        <p role="alert" className="max-w-xl text-center text-sm text-red-700">
          {state.error}
        </p>
      )}
    </div>
  );
}
