import { defineConfig } from 'cypress';
import baseViteConfig from './vite.config';

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    video: false,
    screenshotOnRunFailure: true,
    screenshotsFolder: 'cypress/screenshots',
    supportFile: 'cypress/support/e2e.ts',
    specPattern: 'cypress/e2e/**/*.cy.{js,ts}',
  },
  component: {
    devServer: {
      framework: 'react',
      bundler: 'vite',
      viteConfig: async (baseConfig) => {
        return {
          ...baseConfig,
          define: {
            ...baseConfig.define,
            'process.env.NODE_ENV': JSON.stringify('test'),
          },
        };
      },
    },
    video: false,
    screenshotOnRunFailure: true,
    screenshotsFolder: 'cypress/screenshots',
    specPattern: 'cypress/component/**/*.cy.{js,ts,tsx}',
    supportFile: 'cypress/support/component.ts',
  },
  env: {
    VIDEO: false,
  },
});
