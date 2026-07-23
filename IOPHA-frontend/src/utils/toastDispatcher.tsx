import { toast } from "react-toastify";
import { ProblemDetailError, getToastId, getSeverity, getAutoClose, getPlacement } from "./api";

export function dispatchError(error: ProblemDetailError, placement?: "chat" | "top-right") {
  const toastId = getToastId(error);
  const type = getSeverity(error);
  const resolvedPlacement = placement || getPlacement(error);
  const autoClose = getAutoClose(error);

  const message = `${error.requestId?.substring(0, 8) || "unknown"}... ${error.detail || "Something went wrong. Please try again."}`;

  const content = (
    <div>
      <p>{message}</p>
      {error.help_url && (
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
    containerId: resolvedPlacement,
    autoClose,
    hideProgressBar: false,
  });
}
