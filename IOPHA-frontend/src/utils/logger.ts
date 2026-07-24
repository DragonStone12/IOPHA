class Logger {
  private static isProd = !import.meta.env.DEV;

  static debug(message: string, ...args: unknown[]): void {
    if (!Logger.isProd) {
      console.debug("[DEBUG]", message, ...args);
    }
  }

  static info(message: string, ...args: unknown[]): void {
    if (!Logger.isProd) {
      console.info("[INFO]", message, ...args);
    }
  }

  static warn(message: string, ...args: unknown[]): void {
    if (!Logger.isProd) {
      console.warn("[WARN]", message, ...args);
    }
  }

  static error(message: string, ...args: unknown[]): void {
    console.error("[ERROR]", message, ...args);
  }

  static apiFailure(error: {
    title: string;
    status: number;
    instance: string;
    requestId?: string;
  }): void {
    const logEntry = {
      title: error.title,
      status: error.status,
      instance: error.instance,
      requestId: error.requestId,
    };

    if (error.status === 400 || error.status === 422) {
      Logger.warn("[API_FAILURE]", logEntry);
    } else {
      Logger.error("[API_FAILURE]", logEntry);
    }
  }
}

const appRenderDebug = !import.meta.env.DEV
  ? () => {}
  : (...args: unknown[]) => console.debug("[APP:RENDER]", ...args);

const appApiDebug = !import.meta.env.DEV
  ? () => {}
  : (...args: unknown[]) => console.debug("[APP:API]", ...args);

const appRouterDebug = !import.meta.env.DEV
  ? () => {}
  : (...args: unknown[]) => console.debug("[APP:ROUTER]", ...args);

export { appRenderDebug, appApiDebug, appRouterDebug };
export default Logger;
export const debug: typeof Logger.debug = Logger.debug;
export const info: typeof Logger.info = Logger.info;
export const warn: typeof Logger.warn = Logger.warn;
export const error: typeof Logger.error = Logger.error;
export const apiFailure: typeof Logger.apiFailure = Logger.apiFailure;
