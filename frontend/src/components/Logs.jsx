const statusStyles = {
  waiting: "bg-zinc-100 text-zinc-500",
  writing: "bg-amber-50 text-amber-700 animate-pulse",
  ready: "bg-green-50 text-green-700",
};

export default function StatusPage({
  logs = [],
  sections = [],
  title = "Your blog",
  error = "",
  onCancel,
  onStartOver,
}) {
  const completed = logs.filter((log) => log.status === "ready").length;
  const total = sections.length;
  const progress = total ? Math.round((completed / total) * 100) : 0;
  const statusMessage =
    total > 0 && completed === total
      ? "All sections are written. Assembling the article..."
      : `Completed ${completed} of ${total} sections`;

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-3xl flex-col justify-center gap-5 px-4 py-8 sm:px-6">
      <header className="border-b border-zinc-200 pb-4">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <span className="text-xs font-semibold uppercase tracking-[0.16em] text-green-800">
              Writing your blog
            </span>
            <span className="text-sm font-medium text-zinc-500">
              {progress}%
            </span>
          </div>
          {!error && (
            <button
              type="button"
              onClick={onCancel}
              className="rounded-full px-3 py-2 text-sm font-semibold text-red-700 transition hover:bg-red-50 hover:text-red-800 cursor-pointer"
            >
              Cancel
            </button>
          )}
        </div>
        <h1 className="mt-3 text-2xl font-semibold tracking-tight text-zinc-900">
          {title}
        </h1>
        <div className="mt-4 h-2 overflow-hidden rounded-full bg-zinc-100">
          <div
            className="h-full rounded-full bg-green-700 transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="mt-2 text-sm text-zinc-600">{statusMessage}</p>
      </header>

      <section className="rounded-2xl border-2 border-zinc-200 bg-white p-5 shadow-sm">
        <ol className="grid gap-3 sm:grid-cols-2">
          {sections.map((section) => {
            const log = logs.find((item) => item.sectionId === section.id);
            const status = log?.status || "waiting";

            return (
              <li
                key={section.id}
                className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3 rounded-xl border border-zinc-100 p-3"
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
      </section>
      {error && (
        <div
          role="alert"
          className="flex flex-col gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800 sm:flex-row sm:items-center sm:justify-between"
        >
          <p>{error}</p>
          <button
            type="button"
            onClick={onStartOver}
            className="self-start rounded-full border border-red-300 px-4 py-2 font-semibold transition hover:bg-red-100 sm:self-auto"
          >
            Start over
          </button>
        </div>
      )}
    </main>
  );
}
