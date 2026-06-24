import { defineConfig } from "cypress";
import createBundler from "@bahmutov/cypress-esbuild-preprocessor";
import { addCucumberPreprocessorPlugin } from "@badeball/cypress-cucumber-preprocessor";
import { createEsbuildPlugin } from "@badeball/cypress-cucumber-preprocessor/esbuild";
import { addCucumberWatchAllowList } from "@badeball/cypress-cucumber-preprocessor";

export default defineConfig({
  e2e: {
    video: false,
    screenshotOnRunFailure: true,
    screenshotsFolder: "cypress/screenshots",
    supportFile: "cypress/support/e2e.ts",
    specPattern: "cypress/e2e/Tests/**/*.feature",
    baseUrl: "http://localhost:3000",
    async setupNodeEvents(on, config) {
      await addCucumberPreprocessorPlugin(on, config, {
        stepDefinitions: [
          "cypress/e2e/Tests/*.steps.ts",
          "cypress/support/step_definitions/**/*.{js,ts,tsx}",
        ],
      });
      on(
        "file:preprocessor",
        createBundler({
          plugins: [createEsbuildPlugin(config)],
        })
      );
      return config;
    },
  },
  env: {
    VIDEO: false,
  },
});