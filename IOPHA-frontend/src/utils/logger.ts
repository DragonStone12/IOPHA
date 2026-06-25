class Logger {
  private static isProd = import.meta.env.PROD;

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
}

const appRenderDebug = import.meta.env.PROD
  ? () => {}
  : (...args: unknown[]) => console.debug("[APP:RENDER]", ...args);

const appApiDebug = import.meta.env.PROD
  ? () => {}
  : (...args: unknown[]) => console.debug("[APP:API]", ...args);

const appRouterDebug = import.meta.env.PROD
  ? () => {}
  : (...args: unknown[]) => console.debug("[APP:ROUTER]", ...args);

export { appRenderDebug, appApiDebug, appRouterDebug };
export default Logger;
export const debug: typeof Logger.debug = Logger.debug;
export const info: typeof Logger.info = Logger.info;
export const warn: typeof Logger.warn = Logger.warn;
export const error: typeof Logger.error = Logger.error;
