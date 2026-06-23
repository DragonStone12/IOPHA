import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    video: false,
    screenshotOnRunFailure: true,
    screenshotsFolder: 'cypress/screenshots',
    supportFile: 'cypress/support/e2e.ts',
    specPattern: 'cypress/e2e/**/*.cy.{js,ts}',
  },
  env: {
    VIDEO: false,
  },
});
