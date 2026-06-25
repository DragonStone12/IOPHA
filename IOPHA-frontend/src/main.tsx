import React, { Profiler } from "react";
import ReactDOM from "react-dom/client";
import {
  onRenderCallback,
  logPagePerformanceMetrics,
} from "./utils/performance";
import { appRenderDebug } from "./utils/logger";

appRenderDebug("Mounting IOPHA application root");

const rootElement = document.getElementById("root")!;

const App = (
  <React.StrictMode>
    <h1>IOPHA - Interactive Obesity Prevention Health Assistant</h1>
  </React.StrictMode>
);

const root = ReactDOM.createRoot(rootElement);

logPagePerformanceMetrics();

root.render(
  <Profiler id="IOPHA-App" onRender={onRenderCallback}>
    {App}
  </Profiler>,
);
