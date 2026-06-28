import { useEffect, useRef, useLayoutEffect } from "react";
import logger from "./logger";

const RENDER_THRESHOLD_MS = 16;
const PRODUCTION_SAMPLE_RATE = 0.01;

const isProd = !import.meta.env.DEV;

export const shouldSample = () => {
  if (!isProd) return true;
  return Math.random() < PRODUCTION_SAMPLE_RATE;
};

export const onRenderCallback = (
  id,
  phase,
  actualDuration,
  baseDuration,
  startTime,
  commitTime,
) => {
  if (!shouldSample()) return;

  const meta = {
    id,
    phase,
    actualDuration: Number(actualDuration.toFixed(2)),
    baseDuration: Number(baseDuration.toFixed(2)),
    startTime: Number(startTime.toFixed(2)),
    commitTime: Number(commitTime.toFixed(2)),
  };

  if (actualDuration > RENDER_THRESHOLD_MS) {
    logger.warn("Component render exceeded threshold", meta);
  } else {
    logger.debug("Component render", meta);
  }
};

export const usePerformanceTracking = () => {
  const startTimeRef = useRef(performance.now());
  const renderTimeRef = useRef(0);

  useLayoutEffect(() => {
    startTimeRef.current = performance.now();
  });

  useEffect(() => {
    const endTime = performance.now();
    renderTimeRef.current = endTime - startTimeRef.current;

    if (renderTimeRef.current > RENDER_THRESHOLD_MS && shouldSample()) {
      logger.warn("Component render exceeded 16ms threshold", {
        renderTime: Number(renderTimeRef.current.toFixed(2)),
      });
    }
  });

  return renderTimeRef;
};

export const logPagePerformanceMetrics = () => {
  if (!shouldSample()) return;

  const navigation = window.performance.getEntriesByType("navigation")[0];
  if (!navigation) {
    logger.debug("No Navigation Timing entry available");
    return;
  }

  const paint = window.performance.getEntriesByType("paint");
  const firstPaint =
    paint.find((entry) => entry.name === "first-paint")?.startTime ?? null;
  const firstContentfulPaint =
    paint.find((entry) => entry.name === "first-contentful-paint")?.startTime ??
    null;

  const metrics = {
    dns: Number(
      (navigation.domainLookupEnd - navigation.domainLookupStart).toFixed(2),
    ),
    tcp: Number((navigation.connectEnd - navigation.connectStart).toFixed(2)),
    ttfb: Number(
      (navigation.responseStart - navigation.requestStart).toFixed(2),
    ),
    domInteractive: Number(navigation.domInteractive.toFixed(2)),
    domContentLoaded: Number(navigation.domContentLoadedEventEnd.toFixed(2)),
    loadComplete: Number(navigation.loadEventEnd.toFixed(2)),
    firstPaint,
    firstContentfulPaint,
  };

  logger.info("Page performance metrics", metrics);
};
