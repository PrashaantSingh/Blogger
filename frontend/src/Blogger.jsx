import { useState } from "react";

import InputPage from "./components/InputPage";
import StatusPage from "./components/Logs";
import ResultsPage from "./components/ResultBlog";
import PlanApproval from "./components/PlanApproval";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function Blogger() {
  const [currentView, setCurrentView] = useState("input");
  // const [currentView, setCurrentView] = useState("approval");
  const [topic, setTopic] = useState("");
  const [logs, setLogs] = useState([]);
  const [blogTitle, setBlogTitle] = useState("");
  const [blogContent, setBlogContent] = useState("");
  const [error, setError] = useState("");
  const [proposal, setProposal] = useState(null);

  const handleEvent = (event) => {
    if (event.error) {
      throw new Error(event.detail || event.error);
    }
    if (event.finished) {
      setBlogContent(event.blog);
      setBlogTitle(event.blog_title);
      setCurrentView("results");
      return;
    }
    if (event.name === "start") return;

    setLogs((previous) => {
      const index = previous.findIndex((log) => log.id === event.id);
      if (index === -1) return [...previous, event];
      const next = [...previous];
      next[index] = {
        ...next[index],
        ...event,
        status: event.name === "worker" ? "ready" : next[index].status,
        message: event.name === "worker" ? "Ready" : event.message,
      };
      return next;
    });
  };

  const handleStartGeneration = async (selectedTopic, supporting_documents) => {
    setTopic(selectedTopic);
    setCurrentView("planning");
    setLogs([]);
    setBlogTitle("");
    setBlogContent("");
    setError("");
    setProposal(null);

    try {
      const formData = new FormData();

      formData.append("topic", selectedTopic);

      if (supporting_documents?.length) {
        supporting_documents.forEach((file) => {
          formData.append("supporting_documents", file);
        });
      }

      const response = await fetch(`${API_URL}/plan`, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        let detail = "";
        try {
          const body = await response.json();
          detail =
            typeof body.detail === "string"
              ? body.detail
              : Array.isArray(body.detail)
                ? body.detail.map((item) => item.msg).join(", ")
                : "";
        } catch {
          detail = "";
        }
        throw new Error(
          detail || `Planning request failed (${response.status})`,
        );
      }
      setProposal(await response.json());
      setCurrentView("approval");
    } catch (planningError) {
      setError(
        planningError instanceof Error
          ? planningError.message
          : "Unable to create a blog plan.",
      );
      setCurrentView("input");
    }
  };

  const handleApprove = async () => {
    setCurrentView("status");
    setLogs(
      proposal.sections.map((section) => ({
        id: `section-${section.id}`,
        section: section.title,
        sectionId: section.id,
        name: "section",
        message: "Writing",
        status: "writing",
      })),
    );
    try {
      const response = await fetch(
        `${API_URL}/generate?approval_id=${encodeURIComponent(proposal.approval_id)}`,
      );
      if (!response.ok)
        throw new Error(`Generation request failed (${response.status})`);
      if (!response.body) throw new Error("Readable stream is not supported");
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      const processLine = (line) => {
        if (!line.trim()) return;
        try {
          handleEvent(JSON.parse(line));
        } catch (eventError) {
          if (eventError instanceof SyntaxError) {
            console.error("Invalid workflow event:", line);
            return;
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
    } catch (generationError) {
      console.error("Streaming error:", generationError);
      setError(
        generationError instanceof Error
          ? generationError.message
          : "Unable to generate the blog.",
      );
      setCurrentView("input");
    }
  };

  if (currentView === "planning") {
    return <StatusPage logs={[]} topic={topic} />;
  }

  if (currentView === "approval") {
    return (
      <PlanApproval
        proposal={proposal}
        onApprove={handleApprove}
        onReject={() => setCurrentView("input")}
      />
    );
  }

  if (currentView === "status") {
    return (
      <StatusPage
        logs={logs}
        sections={proposal?.sections || []}
        topic={topic}
      />
    );
  }

  if (currentView === "results") {
    return (
      <ResultsPage
        blog_title={blogTitle || topic}
        blogContent={blogContent}
        onReset={() => setCurrentView("input")}
      />
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-8 p-6">
      <InputPage onSubmit={handleStartGeneration} />
      {error && (
        <p role="alert" className="max-w-xl text-center text-sm text-red-700">
          {error}
        </p>
      )}
    </div>
  );
}
