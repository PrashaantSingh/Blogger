export default function PlanApproval({ proposal, onApprove, onReject }) {
  return (
    <main className="w-full max-w-7xl bg-white p-6 shadow-sm sm:p-8 mx-auto">
      <div className="mb-6 border-b border-zinc-100 pb-5">
        <p className="text-xs font-mono uppercase tracking-widest text-green-800">
          Review before writing
        </p>
        <h1 className="mt-2 text-2xl font-bold tracking-tight text-zinc-900">
          {proposal.blog_title}
        </h1>
        <p className="mt-2 text-sm leading-6 text-zinc-500">
          Review the proposed outline to start the blog generation.
        </p>
        {proposal.document_name && (
          <p className="mt-3 rounded-lg bg-green-50 px-3 py-2 text-xs text-green-800">
            Using information from: <strong>{proposal.document_name}</strong>
          </p>
        )}
      </div>

      <ol className="flex flex-col gap-2">
        {proposal.sections.map((section) => (
          <li
            key={section.id}
            className="rounded-2xl border border-zinc-200 bg-zinc-50 p-4"
          >
            <div className="flex gap-3">
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-zinc-900 text-xs font-semibold text-white">
                {section.id}
              </span>
              <div className="min-w-0">
                <h2 className="font-semibold text-zinc-900">{section.title}</h2>
                <p className="mt-1 text-sm leading-5 text-zinc-600">
                  {section.brief}
                </p>
              </div>
            </div>
          </li>
        ))}
      </ol>

      <div className="mt-7 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
        <button
          type="button"
          onClick={onReject}
          className="rounded-full border border-zinc-300 px-5 py-3 text-sm font-semibold text-zinc-700 transition hover:bg-zinc-100"
        >
          Change topic
        </button>
        <button
          type="button"
          onClick={onApprove}
          className="rounded-full bg-zinc-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-zinc-700"
        >
          Approve and write
        </button>
      </div>
    </main>
  );
}
