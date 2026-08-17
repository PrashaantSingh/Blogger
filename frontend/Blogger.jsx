// import React, { useEffect, useState } from "react";

// export default function Blogger() {
//   const [logs, setLogs] = useState([]);
//   const [blogContent,setBlogContent]=useState('')

//   useEffect(() => {
//     async function getState() {
//       const res = await fetch("http://localhost:8000/generate");
//       if(!res.body)throw new Error("Readable stream not supported")

//       const reader=res.body.getReader()
//       const decoder=new TextDecoder()
//       let buffer=''
//       while(true){
//         const {value,done}=await reader.read()
//         if(done)break;

//         buffer+=decoder.decode(value,{stream:true})
//         const lines=buffer.split('\n')
//         buffer=lines.pop()

//       }

//     }

//   }, []);
//   return (
//     <div className="h-screen flex flex-col gap-20 items-center justify-center">
//       {/* <StatusPage /> */}
//       <InputPage />
//     </div>
//     // <ResultsPage />
//   );
// }

// function InputPage() {
//   const [topic, setTopic] = useState("");
//   function handleChange(e) {
//     setTopic(e.target.value);
//   }

//   function handleClick() {
//     console.log("sending the topic to the llm...");
//     console.log(topic);
//   }
//   return (
//     <>
//       <h1 className="text-6xl">Blogger.</h1>
//       <div className="border-dashed border rounded-full relative w-[50%] mx-auto flex items-center">
//         <input
//           className="p-5 w-full rounded-full outline-none"
//           type="text"
//           placeholder="Enter the topic for the Blog"
//           value={topic}
//           onChange={(e) => handleChange(e)}
//         />
//         <button
//           className={`p-5 text-white font-semibold rounded-r-full absolute right-0 ${topic.trim() == "" ? "bg-gray-500 cursor-not-allowed" : "bg-gray-950 cursor-pointer"}`}
//           onClick={handleClick}
//         >
//           write
//         </button>
//       </div>
//     </>
//   );
// }
// function StatusPage() {
//   const initialStatus = [
//     "Analyzing the topic...",
//     "Generating the outline...",
//     "Writing content for Section 1...",
//     "Drafting content for Section 2...",
//     "Stitching all content together...",
//     "Finalizing the complete draft...",
//   ];
//   const [status, setStatus] = useState("");

//   useEffect(() => {
//     for (let i = 0; i < initialStatus.length; i++) {
//       setTimeout(() => setStatus(initialStatus[i]), i * 2000);
//     }
//   }, []);
//   //
//   return <div className="animate-bounce">{status}</div>;
// }

// const outputBlog = {
//   blogTitle: "The Future of Remote Work: Productivity vs. Isolation",
//   metaData: {
//     author: "AI Agent",
//     datePublished: "2023-10-27",
//     tags: ["remote work", "productivity", "mental health"],
//   },
//   sections: [
//     {
//       section_id: "H1",
//       title: "Introduction: The Great Shift to Remote Work",
//       content_text:
//         "The global shift towards remote work has fundamentally redefined the modern professional landscape, offering unprecedented flexibility. This document will explore the dual nature of this revolution.",
//       summary:
//         "Sets the stage for the article by defining the scope of remote work.",
//     },
//     {
//       section_id: "H2",
//       title: "Productivity Gains: The Freedom of Home Office",
//       content_text:
//         "One of the most celebrated advantages of remote work is the dramatic increase in personal productivity, as employees benefit from reduced commute times. Studies show that focused, uninterrupted home environments significantly boost deep work capabilities.",
//       summary: "Details the benefits related to time saving and focus.",
//     },
//     {
//       section_id: "H3",
//       title: "The Isolation Factor: Mental Health Challenges",
//       content_text:
//         "However, this freedom comes at a cost. The lack of spontaneous social interaction and the blurring of work-life boundaries can lead to feelings of isolation and burnout.",
//       summary:
//         "Discusses the negative side effects and mental health concerns.",
//     },
//     {
//       section_id: "H4",
//       title: "Tools and Strategies for Balanced Remote Life",
//       content_text:
//         "To combat isolation, establishing strict boundaries (like dedicated 'off' hours) and intentionally scheduling social breaks are vital strategies for long-term success.",
//       summary: "Provides actionable advice for balancing work and life.",
//     },
//   ],
//   finalSummary:
//     "A comprehensive overview of the pros and cons of remote work, concluding with actionable balance tips.",
// };
// function ResultsPage() {
//   return (
//     <div className="w-[60%] mx-auto mt-4">
//       <h1 className="text-4xl font-bold">{outputBlog.blogTitle}</h1>
//       <div>
//         {outputBlog.sections.map((sec) => {
//           return (
//             <div className="my-4">
//               <h2 className="text-2xl font-semibold">{sec.title}</h2>
//               <p className="text-lg">{sec.content_text}</p>
//             </div>
//           );
//         })}
//       </div>
//     </div>
//   );
// }

import InputPage from "./src/components/InputPage";
import StatusPage from "./src/components/Logs";
import ResultsPage from "./src/components/ResultBlog";

import { useState } from "react";

export default function Blogger() {
  const [currentView, setCurrentView] = useState("input"); // 'input', 'status', or 'results'
  const [topic, setTopic] = useState(
    "write a blog on Agentic Ai in 2026 also mention how it is being so much helpful",
  );
  const [logs, setLogs] = useState([]);
  const [blog_title, setBlogTitle] = useState("");
  const [blogContent, setBlogContent] = useState("");

  const handleStartGeneration = async (selectedTopic) => {
    setTopic(selectedTopic);
    setCurrentView("status");
    setLogs([]);
    setBlogContent("");

    try {
      const response = await fetch(
        `http://localhost:8000/generate?topic=${encodeURIComponent(selectedTopic)}`,
      );
      if (!response.body) throw new Error("Readable stream not supported");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const jsonObject = JSON.parse(line);
            if (jsonObject.finished) {
              setBlogContent(jsonObject.blog);
              setBlogTitle(jsonObject.blog_title);
              setTimeout(() => setCurrentView("results"), 1000);
            } else {
              setLogs((prev) => {
                const existingIndex = prev.findIndex(
                  (log) => log.id === jsonObject.id,
                );
                if (existingIndex > -1) {
                  const updated = [...prev];
                  updated[existingIndex] = jsonObject;
                  return updated;
                }
                return [...prev, jsonObject];
              });
            }
          } catch (err) {
            console.error("Failed to parse line:", line);
          }
        }
      }
    } catch (error) {
      console.error("Streaming error:", error);
      setCurrentView("input");
    }
  };

  return (
    <div className="h-screen flex flex-col gap-20 items-center justify-center">
      {currentView === "input" && (
        <InputPage onSubmit={handleStartGeneration} />
      )}
      {currentView === "status" && <StatusPage logs={logs} topic={topic} />}
      {currentView === "results" && (
        <ResultsPage
          blog_title={
            blog_title ||
            `${topic.length > 30 ? topic.substring(0, 25) + "..." + topic.split(" ").at(-1) : topic}`
          }
          blogContent={blogContent}
          onReset={() => setCurrentView("input")}
        />
      )}
    </div>
  );
}
