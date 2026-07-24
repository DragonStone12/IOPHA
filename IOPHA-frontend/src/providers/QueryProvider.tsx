import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { ProblemDetailError } from "../utils/api";
import { dispatchError } from "../utils/toastDispatcher";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      gcTime: 1000 * 60 * 15,
      retry: 1,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
});

queryClient.getQueryCache().config.onError = (error) => {
  if (error instanceof ProblemDetailError) {
    dispatchError(error);
  } else {
    const message = error instanceof Error ? error.message : String(error);
    dispatchError(
      new ProblemDetailError(
        { status: 500, title: "Internal Server Error", detail: message },
      ),
    );
  }
};

queryClient.getMutationCache().config.onError = (error) => {
  if (error instanceof ProblemDetailError) {
    dispatchError(error);
  } else {
    const message = error instanceof Error ? error.message : String(error);
    dispatchError(
      new ProblemDetailError(
        { status: 500, title: "Internal Server Error", detail: message },
      ),
    );
  }
};

export function QueryProvider({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  );
}
