export default function OutlineLoadingPage({ onCancel, error = "" }) {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-3xl flex-col justify-center gap-5 px-4 py-8 text-zinc-900 sm:px-6">
      <header className="flex items-start justify-between gap-4 border-b border-zinc-200 pb-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-green-800">
            Preparing your outline
          </p>
          <p className="mt-2 text-sm leading-6 text-zinc-600">
            Creating a title and outline for your blog.
          </p>
        </div>
        <button
          type="button"
          onClick={onCancel}
          className="shrink-0 rounded-full px-3 py-2 text-sm font-semibold text-red-700 transition hover:bg-red-50 hover:text-red-800 cursor-pointer"
        >
          Cancel
        </button>
      </header>

      <section
        aria-live="polite"
        className="flex items-center gap-4 rounded-2xl border-2 border-zinc-200 bg-white p-5 shadow-sm"
      >
        <div className="flex min-w-0 flex-1 items-center gap-2">
          <span className="h-1.5 flex-1 animate-pulse rounded-full bg-green-200" />
          <span className="h-1.5 flex-1 animate-pulse rounded-full bg-green-300 [animation-delay:150ms]" />
          <span className="h-1.5 flex-1 animate-pulse rounded-full bg-green-400 [animation-delay:300ms]" />
        </div>
      </section>
      {error && (
        <p role="alert" className="text-sm text-red-700">
          {error}
        </p>
      )}
    </main>
  );
}
