import { useEffect, useRef } from "react";
import Logger from "../utils/logger";

export function useLogRenders(
  componentName: string,
  trackedProps?: Record<string, unknown>,
): void {
  const renderCount = useRef(0);

  useEffect(() => {
    renderCount.current += 1;
    Logger.debug(`${componentName} rendered`, {
      count: renderCount.current,
      props: trackedProps,
    });
  });
}
