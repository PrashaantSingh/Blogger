// import ReactMarkdown from "react-markdown";
// export default function ResultsPage({blog_title, blogContent, onReset }) {
//     console.log(blogContent)
//     console.log(blog_title)
//   return (
//     <div className="w-[80%] overflow-y-auto mx-auto gap-6 p-4 ">
//       <div className="flex justify-between items-center border-b border-zinc-200 pb-4">
//         <h1 className="text-3xl font-mono uppercase">
//           {blog_title}
//         </h1>
//         <button
//           onClick={onReset}
//           className="px-4 py-3 border border-zinc-300 rounded-full text-xs font-medium text-zinc-800 hover:bg-zinc-100 transition cursor-pointer"
//         >
//           Write another
//         </button>
//       </div>

//       <article className="">
//         <ReactMarkdown
//           components={{
//             h1: ({ children }) => (
//               <h1 className="text-2xl font-bold mb-6">{children}</h1>
//             ),
//             h2: ({ children }) => (
//               <h2 className="text-xl font-semibold mt-8 mb-4">{children}</h2>
//             ),
//             p: ({ children }) => (
//               <p className="text-lg leading-8 mb-4">{children}</p>
//             ),
//           }}
//         >
//           {blogContent}
//         </ReactMarkdown>
//       </article>
//     </div>
//   );
// }
import { useEffect } from "react";
import ReactMarkdown from "react-markdown";

export default function ResultsPage({ blog_title, blogContent, onReset }) {
  // 1. Automatically scroll back to top whenever new results load
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "instant" });
  }, [blogContent]);

  return (
    <main className="min-h-screen w-full bg-white text-zinc-900 pt-8 pb-16 px-4 sm:px-6 md:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-200 pb-6 mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-zinc-900 leading-tight">
            {blog_title}
          </h1>
          <button
            onClick={onReset}
            className="self-start sm:self-auto px-5 py-2.5 bg-zinc-900 text-white rounded-full text-xs font-semibold hover:bg-zinc-800 transition active:scale-95 cursor-pointer whitespace-nowrap"
          >
            Write another
          </button>
        </header>

        {/* Blog Article Content */}
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
            {blogContent}
          </ReactMarkdown>
        </article>
      </div>
    </main>
  );
}