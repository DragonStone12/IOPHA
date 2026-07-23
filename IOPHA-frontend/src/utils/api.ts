export interface ProblemDetail {
  title?: string;
  status?: number;
  detail?: string;
  instance?: string;
  help_url?: string;
}

export class ProblemDetailError extends Error {
  public readonly status: number;
  public readonly title: string;
  public readonly detail: string;
  public readonly instance: string;
  public readonly help_url?: string;
  public readonly requestId?: string;

  constructor(payload: { status: number; title: string; detail?: string; instance?: string; help_url?: string }, requestId?: string) {
    const { status, title, detail, instance, help_url } = payload;
    super(title);
    this.name = "ProblemDetailError";
    this.status = status;
    this.title = title;
    this.detail = detail || "";
    this.instance = instance || "";
    this.help_url = help_url;
    this.requestId = requestId;
  }
}

function kebabCase(str: string): string {
  return str
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-");
}

export function getToastId(error: ProblemDetailError): string {
  return `${kebabCase(error.title)}${error.instance}`;
}

export function getSeverity(error: ProblemDetailError): "error" | "warning" | "info" {
  const titleOverrides: Record<string, "error" | "warning" | "info"> = {
    "Search Aggregator Timeout": "warning",
    "Notification Gateway Timeout": "info",
    "WebSocket Connection Drop": "warning",
  };

  if (titleOverrides[error.title]) {
    return titleOverrides[error.title];
  }

  if (error.status === 0 || error.status === 409 || error.status === 410) {
    return "warning";
  }

  return "error";
}

export function getAutoClose(error: ProblemDetailError): number | false {
  if (getSeverity(error) === "error") {
    return false;
  }
  return 5000;
}

export function getPlacement(error: ProblemDetailError): "chat" | "top-right" {
  const chatTitles = new Set([
    "Nutrition Evaluation Error",
    "Search Aggregator Timeout",
    "WebSocket Connection Drop",
    "Payload Too Large",
    "Notification Gateway Timeout",
    "Out of Order Message Delivery",
    "Unread Notification Inconsistency",
  ]);

  if (chatTitles.has(error.title)) {
    return "chat";
  }

  return "top-right";
}

export async function apiFetch<T>(url: string, options: RequestInit = {}): Promise<T> {
  const requestId = crypto.randomUUID();
  const headers = new Headers(options.headers);
  headers.set("X-Request-ID", requestId);

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.ok) {
      return response.json();
    }

    let parsed: unknown = null;
    let parsedOk = false;

    try {
      parsed = await response.json();
      parsedOk = true;
    } catch {
      parsedOk = false;
    }

    if (parsedOk && parsed && typeof parsed === "object" && "title" in parsed && "status" in parsed) {
      const problemDetail = parsed as Partial<ProblemDetail>;
      throw new ProblemDetailError(
        {
          status: response.status,
          title: problemDetail.title!,
          detail: problemDetail.detail,
          instance: problemDetail.instance,
          help_url: problemDetail.help_url,
        },
        response.headers.get("X-Request-ID") || requestId,
      );
    }

    if (response.status >= 500) {
      throw new ProblemDetailError(
        { status: response.status, title: "Service Unavailable" },
        requestId,
      );
    }

    throw new ProblemDetailError(
      { status: response.status, title: "Unexpected Error" },
      requestId,
    );
  } catch (error) {
    if (error instanceof ProblemDetailError) {
      throw error;
    }

    throw new ProblemDetailError({ status: 0, title: "Network Unreachable" }, requestId);
  }
}
