import { ErrorBoundary, FallbackProps } from "react-error-boundary";
import Logger from "../utils/logger";

// Keep the fallback UI extremely simple to prevent secondary crashes
function ErrorFallback({ error, resetErrorBoundary }: FallbackProps) {
  return (
    <div
      role="alert"
      className="p-4 border border-red-500 bg-red-50 text-red-800 rounded max-w-md m-4"
    >
      <h2 className="font-bold text-lg">Something went wrong</h2>
      <pre className="text-sm mt-2 whitespace-pre-wrap break-words">
        {error.message}
      </pre>
      <button
        onClick={resetErrorBoundary}
        className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
      >
        Try again
      </button>
    </div>
  );
}

interface AppErrorBoundaryProps {
  children: React.ReactNode;
  boundaryName?: string; // Used for log context
}

export function AppErrorBoundary({
  children,
  boundaryName = "App",
}: AppErrorBoundaryProps) {
  const handleError = (
    error: Error,
    info: { componentStack: string | null },
  ) => {
    // Integrate with the custom Logger created in the previous story
    Logger.error(`[ErrorBoundary: ${boundaryName}] caught a render error`, {
      errorMessage: error.message,
      errorStack: error.stack,
      componentStack: info.componentStack,
    });
  };

  return (
    <ErrorBoundary FallbackComponent={ErrorFallback} onError={handleError}>
      {children}
    </ErrorBoundary>
  );
}
