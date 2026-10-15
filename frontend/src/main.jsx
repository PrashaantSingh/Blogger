import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";

import Blogger from "./Blogger.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <Blogger />
  </StrictMode>,
);
