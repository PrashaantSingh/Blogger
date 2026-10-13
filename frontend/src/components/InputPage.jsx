import { useState } from "react";

export default function InputPage({ onSubmit }) {
  const [topic, setTopic] = useState("");
  const [files, setFiles] = useState(null);

  function handleClick() {
    if (!topic.trim()) return;
    onSubmit(topic, files);
  }

  return (
    <div className="w-full max-w-3xl flex flex-col items-center gap-8">
      <h1 className="text-6xl font-extrabold tracking-tight">Blogger.</h1>
      <div className="border-dashed border-2 border-gray-400 rounded-full w-full flex items-center shadow-sm">
        <input
          className="p-5 pl-8 w-full rounded-full outline-none bg-transparent text-lg"
          type="text"
          placeholder="Enter the topic for the Blog"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleClick()}
        />
        <button
          className={`p-5 px-8 text-white font-semibold rounded-r-full transition-colors ${
            topic.trim() === ""
              ? "bg-gray-400 cursor-not-allowed"
              : "bg-gray-950 hover:bg-gray-800 cursor-pointer"
          }`}
          onClick={handleClick}
        >
          write
        </button>
      </div>
      <label className="w-full cursor-pointer rounded-2xl border border-zinc-200 bg-white px-5 py-4 text-sm text-zinc-600 shadow-sm transition hover:border-zinc-400">
        <span className="font-semibold text-zinc-800">
          Add supporting document
        </span>
        <span className="ml-2 text-zinc-500">
          (supported formats: TXT, Markdown, CSV, PDF, DOCX)
        </span>
        <input
          className="sr-only"
          type="file"
          multiple
          accept=".txt,.md,.csv,.pdf,.docx"
          onChange={(event) => {
            console.log(Array.from(event.target.files));
            setFiles(Array.from(event.target.files) || null);
          }}
        />
        {files &&
          Array.from(files).map((file, i) => (
            <p key={i} className="mt-2 truncate text-xs text-green-800">
              {file.name}
            </p>
          ))}
      </label>
    </div>
  );
}
