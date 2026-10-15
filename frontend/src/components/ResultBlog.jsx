
import { useEffect } from "react";
import ReactMarkdown from "react-markdown";

function removeDuplicateTitle(content, title) {
  const match = content.match(/^\s*#\s+(.+?)(?:\r?\n|$)/);
  if (!match || match[1].trim().toLocaleLowerCase() !== title.trim().toLocaleLowerCase()) {
    return content;
  }

  return content.slice(match[0].length).trimStart();
}

export default function ResultsPage({ blogTitle, blogContent, onReset }) {
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "instant" });
  }, [blogContent]);

  return (
    <main className="min-h-screen w-full bg-white text-zinc-900 pt-8 pb-16 px-4 sm:px-6 md:px-8">
      <div className="max-w-4xl mx-auto">
        <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-200 pb-6 mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-zinc-900 leading-tight">
            {blogTitle}
          </h1>
          <button
            onClick={onReset}
            className="self-start sm:self-auto px-5 py-2.5 bg-zinc-900 text-white rounded-full text-xs font-semibold hover:bg-zinc-800 transition active:scale-95 cursor-pointer whitespace-nowrap"
          >
            Write another
          </button>
        </header>

        <article className="text-zinc-800">
          <ReactMarkdown
            components={{
              h1: ({ children }) => (
                <h1 className="text-2xl sm:text-3xl font-bold text-zinc-900 mt-10 mb-4 first:mt-0">
                  {children}
                </h1>
              ),
              h2: ({ children }) => (
                <h2 className="text-xl sm:text-2xl font-semibold text-zinc-900 mt-8 mb-3 border-b border-zinc-100 pb-2">
                  {children}
                </h2>
              ),
              h3: ({ children }) => (
                <h3 className="text-lg font-semibold text-zinc-800 mt-6 mb-2">
                  {children}
                </h3>
              ),
              p: ({ children }) => (
                <p className="text-base sm:text-lg leading-relaxed text-zinc-700 mb-5">
                  {children}
                </p>
              ),
              ul: ({ children }) => (
                <ul className="list-disc list-inside space-y-2 mb-5 text-zinc-700 text-base sm:text-lg">
                  {children}
                </ul>
              ),
              ol: ({ children }) => (
                <ol className="list-decimal list-inside space-y-2 mb-5 text-zinc-700 text-base sm:text-lg">
                  {children}
                </ol>
              ),
              li: ({ children }) => (
                <li className="leading-relaxed">{children}</li>
              ),
              blockquote: ({ children }) => (
                <blockquote className="border-l-4 border-zinc-300 pl-4 italic text-zinc-600 my-6">
                  {children}
                </blockquote>
              ),
              code: ({ inline, children }) =>
                inline ? (
                  <code className="bg-zinc-100 text-zinc-800 px-1.5 py-0.5 rounded text-sm font-mono">
                    {children}
                  </code>
                ) : (
                  <pre className="bg-zinc-900 text-zinc-100 p-4 rounded-xl overflow-x-auto text-sm font-mono my-6">
                    <code>{children}</code>
                  </pre>
                ),
            }}
          >
            {removeDuplicateTitle(blogContent, blogTitle)}
          </ReactMarkdown>
        </article>
      </div>
    </main>
  );
}
