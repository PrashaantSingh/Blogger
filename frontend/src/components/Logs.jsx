import { useEffect, useRef, useState } from "react";

export default function StatusPage({ logs, topic }) {
  const getTaskLabel = (name) => {
    switch (name) {
      case "generate_outline":
        return "Generating Outline";
      case "writer":
        return "Writing Section";
      case "merge_sections":
        return "Merging Sections";
      default:
        return name;
    }
  };

  const cardRef = useRef(null);
  const [height, setHeight] = useState("auto");

  useEffect(() => {
    if (!cardRef.current) return;

    // Use ResizeObserver for smooth and accurate dynamic height tracking
    const observer = new ResizeObserver(([entry]) => {
      if (entry) {
        setHeight(entry.target.scrollHeight);
      }
    });

    observer.observe(cardRef.current);
    return () => observer.disconnect();
  }, []);

  return (
    <div className="w-full max-w-2xl flex flex-col gap-4">
      {/* Header */}
      <div className="flex justify-between items-baseline border-b border-zinc-200 pb-2">
        <span className="text-md  font-mono uppercase tracking-wider animate-pulse text-green-800">
          Workflow Execution
        </span>
        <span className="text-xs text-zinc-500 truncate max-w-[320px] font-medium">
          {topic}
        </span>
      </div>

      {/* Animated height container */}
      <div
        className="transition-[height] duration-300 ease-in-out"
        style={{ height: typeof height === "number" ? `${height}px` : height }}
      >
        {/* Actual card measured directly */}
        <div
          ref={cardRef}
          className="border-dashed border-2 border-zinc-200 rounded-2xl p-5 bg-white shadow-sm"
        >
          <div className="divide-y divide-zinc-100 flex flex-col">
            {logs.map((log) => (
              <div
                key={log.id}
                className="py-3 first:pt-0 last:pb-0 flex items-center justify-between gap-4"
              >
                <div className="min-w-0 flex items-center gap-3 flex-1">
                  <span className="text-xs font-mono uppercase px-2.5 py-1 rounded bg-zinc-100 text-zinc-600 shrink-0 font-medium">
                    {getTaskLabel(log.name)}
                  </span>

                  <span className="text-sm text-zinc-800 truncate">
                    {log.section ||
                      (log.name === "generate_outline"
                        ? "Generating outline structure"
                        : "Merging draft sections")}
                  </span>
                </div>

                <div className="shrink-0 text-xs font-mono">
                  {log.completed ? (
                    <span className="text-zinc-900 font-semibold">
                      completed
                    </span>
                  ) : (
                    <span className="text-zinc-400 animate-pulse">running</span>
                  )}
                </div>
              </div>
            ))}

            {logs.length === 0 && (
              <div className="py-6 text-center text-xs text-zinc-400 font-mono">
                Initializing agent graph...
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
