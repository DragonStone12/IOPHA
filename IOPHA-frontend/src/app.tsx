import React, { Profiler } from "react";
import ReactDOM from "react-dom/client";
import {
  onRenderCallback,
  logPagePerformanceMetrics,
} from "./utils/performance";
import { appRenderDebug } from "./utils/logger";
import { QueryProvider } from "./providers/QueryProvider";
import { UserDisplay } from "./components/UserDisplay";
import { AppErrorBoundary } from "./components/AppErrorBoundary";

appRenderDebug("Mounting IOPHA application root");

const rootElement = document.getElementById("root")!;

const App = (
  <React.StrictMode>
    <AppErrorBoundary boundaryName="Root">
      <h1>IOPHA - Interactive Obesity Prevention Health Assistant</h1>

      <AppErrorBoundary boundaryName="UserDisplay">
        <UserDisplay />
      </AppErrorBoundary>
    </AppErrorBoundary>
  </React.StrictMode>
);

const root = ReactDOM.createRoot(rootElement);

logPagePerformanceMetrics();

root.render(
  <Profiler id="IOPHA-App" onRender={onRenderCallback}>
    <QueryProvider>{App}</QueryProvider>
  </Profiler>,
);
