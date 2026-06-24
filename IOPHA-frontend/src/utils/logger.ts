const isProd = import.meta.env.PROD;

const logger = {
  debug: (...args) => !isProd && console.debug('[DEBUG]', ...args),
  info: (...args) => console.info('[INFO]', ...args),
  warn: (...args) => console.warn('[WARN]', ...args),
  error: (...args) => console.error('[ERROR]', ...args),
};

const appRenderDebug = !isProd ? (...args) => console.debug('[APP:RENDER]', ...args) : () => {};
const appApiDebug = !isProd ? (...args) => console.debug('[APP:API]', ...args) : () => {};
const appRouterDebug = !isProd ? (...args) => console.debug('[APP:ROUTER]', ...args) : () => {};

export { appRenderDebug, appApiDebug, appRouterDebug };
export default logger;
export const { debug, info, warn, error } = logger;