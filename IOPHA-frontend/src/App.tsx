import React, { Profiler } from "react";
import ReactDOM from "react-dom/client";
import {
  onRenderCallback,
  logPagePerformanceMetrics,
} from "./utils/performance";
import { appRenderDebug } from "./utils/logger";
import { AppErrorBoundary } from "./components/AppErrorBoundary";

appRenderDebug("Mounting IOPHA application root");

const rootElement = document.getElementById("root")!;

function App() {
  return (
    <React.StrictMode>
      <h1>IOPHA - Interactive Obesity Prevention Health Assistant</h1>
    </React.StrictMode>
  );
}

function AppBoundary() {
  return (
    <AppErrorBoundary boundaryName="Root">
      <Profiler id="IOPHA-App" onRender={onRenderCallback}>
        <App />
      </Profiler>
    </AppErrorBoundary>
  );
}

const root = ReactDOM.createRoot(rootElement);

logPagePerformanceMetrics();

root.render(<AppBoundary />);
