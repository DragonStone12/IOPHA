import "./index.css";
import { QueryProvider } from "./providers/QueryProvider";
import { LandingPage } from "./components/LandingPage/LandingPage";
import { AppErrorBoundary } from "./components/AppErrorBoundary";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
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
      <h1 className="text-xl font-semibold mb-4">IOPHA - Interactive Obesity Prevention Health Assistant</h1>

      <AppErrorBoundary boundaryName="UserDisplay">
        <UserDisplay />
      </AppErrorBoundary>

      <AppErrorBoundary boundaryName="LandingPage">
        <LandingPage />
      </AppErrorBoundary>
    </AppErrorBoundary>
    <ToastContainer
      containerId="top-right"
      position="top-right"
      newestOnTop
      limit={3}
      pauseOnFocusLoss
    />
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
