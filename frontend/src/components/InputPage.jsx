import { useState } from "react";

export default function InputPage({ onSubmit }) {
  const [topic, setTopic] = useState("");

  function handleChange(e) {
    setTopic(e.target.value);
  }

  function handleClick() {
    if (!topic.trim()) return;
    onSubmit(topic);
  }

  return (
    <div className="w-full flex flex-col items-center gap-10">
      <h1 className="text-6xl font-extrabold tracking-tight">Blogger.</h1>
      <div className="border-dashed border-2 border-gray-400 rounded-full relative w-[60%] max-w-2xl mx-auto flex items-center shadow-sm">
        <input
          className="p-5 pl-8 w-full rounded-full outline-none bg-transparent text-lg"
          type="text"
          placeholder="Enter the topic for the Blog"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleClick()}
        />
        <button
          className={`p-5 px-8 text-white font-semibold rounded-r-full absolute right-0 transition-colors ${
            topic.trim() === ""
              ? "bg-gray-400 cursor-not-allowed"
              : "bg-gray-950 hover:bg-gray-800 cursor-pointer"
          }`}
          onClick={handleClick}
        >
          write
        </button>
      </div>
    </div>
  );
}
