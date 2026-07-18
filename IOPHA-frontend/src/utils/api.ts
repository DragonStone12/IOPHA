// Global backend API base URL.
//
// Injected at build time via the `VITE_API_URL` environment variable
// (e.g. https://k6bbr9kln1.execute-api.us-east-2.amazonaws.com/prod/iopha).
// Until the app is deployed with that variable set, this is an empty string,
// so relative requests (e.g. fetch("/api/user")) resolve against the current
// origin as-is.
export const API_URL: string = import.meta.env.VITE_API_URL ?? "";

// Build a backend request URL. When API_URL is empty, the path is returned
// unchanged so local/dev requests hit the same origin.
export function apiUrl(path: string): string {
  if (!API_URL) {
    return path;
  }
  return `${API_URL.replace(/\/$/, "")}${path.startsWith("/") ? path : `/${path}`}`;
}
