import "./index.css";
import { QueryProvider } from "./providers/QueryProvider";
import { LandingPage } from "./components/LandingPage/LandingPage";
import { AppErrorBoundary } from "./components/AppErrorBoundary";
import { UserDisplay } from "./components/UserDisplay";
import {
  onRenderCallback,
  logPagePerformanceMetrics,
} from "./utils/performance";
import { appRenderDebug } from "./utils/logger";
import ReactDOM from "react-dom/client";
import React, { Profiler } from "react";

const App = (
  <React.StrictMode>
    <AppErrorBoundary boundaryName="Root">
      <h1>IOPHA - Interactive Obesity Prevention Health Assistant</h1>

      <AppErrorBoundary boundaryName="UserDisplay">
        <UserDisplay />
      </AppErrorBoundary>

      <AppErrorBoundary boundaryName="LandingPage">
        <LandingPage />
      </AppErrorBoundary>
    </AppErrorBoundary>
  </React.StrictMode>
);

const rootElement = document.getElementById("root")!;
const root = ReactDOM.createRoot(rootElement);

appRenderDebug("Mounting IOPHA application root");
logPagePerformanceMetrics();

root.render(
  <Profiler id="IOPHA-App" onRender={onRenderCallback}>
    <QueryProvider>{App}</QueryProvider>
  </Profiler>,
);

export default App;
