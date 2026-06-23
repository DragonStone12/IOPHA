import winston from 'winston';

const isProd = import.meta.env.PROD;

const logger = winston.createLogger({
  level: isProd ? 'error' : 'debug',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: isProd
        ? winston.format.combine(
            winston.format.timestamp(),
            winston.format.errors({ stack: true }),
            winston.format.json()
          )
        : winston.format.combine(
            winston.format.colorize(),
            winston.format.timestamp(),
            winston.format.printf(({ timestamp, level, message, ...meta }) => {
              const metaStr = Object.keys(meta).length ? JSON.stringify(meta) : '';
              return `${timestamp} ${level}: ${message} ${metaStr}`;
            })
          )
    })
  ]
});

const appRenderDebug = !isProd ? require('debug')('app:render') : () => {};
const appApiDebug = !isProd ? require('debug')('app:api') : () => {};
const appRouterDebug = !isProd ? require('debug')('app:router') : () => {};

export { appRenderDebug, appApiDebug, appRouterDebug };
export default logger;
export { debug, info, warn, error } from 'winston';
