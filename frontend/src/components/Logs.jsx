import { useEffect, useRef, useState } from "react";

const statusStyles = {
  waiting: "bg-zinc-100 text-zinc-500",
  writing: "bg-amber-50 text-amber-700",
  ready: "bg-green-50 text-green-700",
};

export default function StatusPage({ logs = [], sections = [], topic = "" }) {
  const cardRef = useRef(null);
  const [height, setHeight] = useState("auto");
  const completed = logs.filter((log) => log.status === "ready").length;
  const total = sections.length;
  const progress = total ? Math.round((completed / total) * 100) : 0;
  const current =
    completed === total && total > 0
      ? "Your outline is complete. Finishing the article..."
      : `Writing ${completed} of ${total} sections`;

  useEffect(() => {
    if (!cardRef.current) return undefined;
    const observer = new ResizeObserver(([entry]) => {
      if (entry) setHeight(entry.target.scrollHeight);
    });
    observer.observe(cardRef.current);
    return () => observer.disconnect();
  }, []);

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-3xl flex-col justify-center gap-5 px-4 py-8 sm:px-6 border-zinc-200">
      <header className="border-b border-zinc-200 pb-4">
        <div className="flex items-center justify-between gap-4">
          <span className="text-sm font-semibold tracking-wide text-green-800">
            Writing your blog
          </span>
          {total > 0 && (
            <span className="text-sm font-medium text-zinc-500">
              {progress}%
            </span>
          )}
        </div>
        <p className="mt-2 truncate text-sm text-zinc-500">{topic}</p>
        {total > 0 && (
          <div className="mt-4 h-2 overflow-hidden rounded-full bg-zinc-100">
            <div
              className="h-full rounded-full bg-green-700 transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}
        <p className="mt-2 text-sm text-zinc-600">
          {total ? current : "Creating your outline..."}
        </p>
      </header>

      <div
        className="transition-[height] duration-300 ease-in-out"
        style={{ height: typeof height === "number" ? `${height}px` : height }}
      >
        <div
          ref={cardRef}
          className="rounded-2xl border-2 border-zinc-200 bg-white p-5 shadow-sm"
        >
          {total > 0 ? (
            <ol className="grid gap-3 sm:grid-cols-2">
              {sections.map((section) => {
                const log = logs.find((item) => item.sectionId === section.id);
                const status = log?.status || "waiting";
                return (
                  <li
                    key={section.id}
                    className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3 rounded-xl border border-zinc-100 border p-3"
                  >
                    <span className="flex h-7 w-7 items-center justify-center rounded-full bg-zinc-900 text-xs font-semibold text-white">
                      {section.id}
                    </span>
                    <span className="min-w-0 truncate text-sm font-medium text-zinc-800">
                      {section.title}
                    </span>
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-semibold ${statusStyles[status]}`}
                    >
                      {status === "ready"
                        ? "Completed"
                        : status === "writing"
                          ? "Writing"
                          : "Waiting"}
                    </span>
                  </li>
                );
              })}
            </ol>
          ) : (
            <p className="py-6 text-center text-sm text-zinc-500">
              Preparing your outline...
            </p>
          )}
        </div>
      </div>
    </main>
  );
}
