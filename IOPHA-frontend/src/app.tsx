import "./index.css";
import { QueryProvider } from "./providers/QueryProvider";
import { LandingPage } from "./components/LandingPage/LandingPage";
import ReactDOM from "react-dom/client";
import React from "react";

function App() {
  return (
    <QueryProvider>
      <LandingPage />
    </QueryProvider>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

export default App;
