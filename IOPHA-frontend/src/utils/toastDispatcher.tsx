import { toast } from "react-toastify";
import { ProblemDetailError, getToastId, getSeverity, getAutoClose } from "./api";

const isValidUrl = (url: string): boolean => {
  try {
    const parsed = new URL(url);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
};

export function dispatchError(error: ProblemDetailError) {
  const toastId = getToastId(error);
  const type = getSeverity(error);
  const autoClose = getAutoClose(error);

  const message = `${error.requestId?.substring(0, 8) || "unknown"}... ${error.detail || "Something went wrong. Please try again."}`;

  const content = (
    <div>
      <p>{message}</p>
      {error.help_url && isValidUrl(error.help_url) && (
        <a
          href={error.help_url}
          target="_blank"
          rel="noopener noreferrer"
          className="block mt-1 text-blue-600 underline text-xs"
        >
          Learn more
        </a>
      )}
    </div>
  );

  toast(content, {
    toastId,
    type,
    containerId: "top-right",
    autoClose,
    hideProgressBar: false,
  });
}
