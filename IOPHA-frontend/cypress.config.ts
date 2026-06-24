import { defineConfig } from 'cypress';
import cucumber from 'cypress-cucumber-preprocessor';

export default defineConfig({
  e2e: {
    video: false,
    screenshotOnRunFailure: true,
    screenshotsFolder: 'cypress/screenshots',
    supportFile: 'cypress/support/e2e.ts',
    specPattern: 'cypress/e2e/Tests/**/*.feature',
    baseUrl: 'http://localhost:3000',
    setupNodeEvents(on, config) {
      on('file:preprocessor', cucumber());
    },
  },
  env: {
    VIDEO: false,
  },
});
