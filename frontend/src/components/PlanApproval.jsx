export default function PlanApproval({
  proposal,
  instructions,
  onInstructionsChange,
  onApprove,
  onRegenerate,
  onCancel,
  error,
}) {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-3xl flex-col gap-5 px-4 py-8 text-zinc-900 sm:px-6">
      <header className="border-b border-zinc-200 pb-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-green-800">
              Review your outline
            </p>
            <h1 className="mt-3 text-2xl font-semibold tracking-tight text-zinc-900 sm:text-3xl">
              {proposal.blog_title}
            </h1>
          </div>
          <button
            type="button"
            onClick={onCancel}
            className="shrink-0 rounded-full px-3 py-2 text-sm font-semibold text-red-700 transition cursor-pointer bg-red-100 hover:bg-red-300"
          >
            Cancel
          </button>
        </div>
        <p className="mt-2 text-sm leading-6 text-zinc-600">
          Approve to start writing, or request changes to the outline.
        </p>
        {proposal.document_name && (
          <p className="mt-3 inline-block rounded-lg bg-zinc-50 px-3 py-2 text-xs text-zinc-600">
            Using information from <strong>{proposal.document_name}</strong>
          </p>
        )}
      </header>

      <section className="rounded-2xl border-2 border-zinc-200 bg-white p-5 shadow-sm">
        <ol className="grid gap-3">
          {proposal.sections.map((section) => (
            <li
              key={section.id}
              className="grid grid-cols-[auto_minmax(0,1fr)] items-start gap-3 rounded-xl border border-zinc-100 p-3"
            >
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-zinc-900 text-xs font-semibold text-white">
                {section.id}
              </span>
              <div className="min-w-0">
                <h2 className="font-semibold text-zinc-900">{section.title}</h2>
                <p className="mt-1 text-sm leading-5 text-zinc-600">
                  {section.brief}
                </p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <label className="block text-sm font-medium text-zinc-700">
        Want to change something?
        <textarea
          value={instructions}
          onChange={(event) => onInstructionsChange(event.target.value)}
          maxLength={2000}
          rows={3}
          placeholder="Enter the instructions for making edits."
          className="mt-2 w-full resize-y rounded-xl border border-zinc-300 px-4 py-3 text-sm font-normal text-zinc-800 outline-none transition focus:border-zinc-500"
        />
      </label>

      {error && (
        <p role="alert" className="text-sm text-red-700">
          {error}
        </p>
      )}
      <div className="flex flex-col-reverse items-start gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex w-full flex-col-reverse gap-3 sm:w-auto sm:flex-row sm:items-center">
          <button
            type="button"
            onClick={() => onRegenerate(instructions)}
            className="px-5 py-3 text-sm font-semibold text-zinc-600 bg-white transition hover:text-zinc-950 cursor-pointer border rounded-full"
          >
            Regenerate outline
          </button>
          <button
            type="button"
            onClick={onApprove}
            className="rounded-full bg-zinc-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-zinc-700 cursor-pointer"
          >
            Approve and write
          </button>
        </div>
      </div>
    </main>
  );
}
