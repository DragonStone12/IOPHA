import { defineConfig } from "cypress";
import createBundler from "@bahmutov/cypress-esbuild-preprocessor";
import { addCucumberPreprocessorPlugin } from "@badeball/cypress-cucumber-preprocessor";
import { createEsbuildPlugin } from "@badeball/cypress-cucumber-preprocessor/esbuild";

export default defineConfig({
  e2e: {
    video: false,
    screenshotOnRunFailure: true,
    screenshotsFolder: "cypress/screenshots",
    supportFile: "cypress/support/e2e.ts",
    specPattern: "cypress/e2e/Tests/**/*.feature",
    baseUrl: "http://localhost:3000",
    async setupNodeEvents(on, config) {
      await addCucumberPreprocessorPlugin(on, config);
      on(
        "file:preprocessor",
        createBundler({
          plugins: [createEsbuildPlugin(config)],
        }),
      );
      const getCompareSnapshotsPlugin = require("cypress-image-diff-js/plugin");
      getCompareSnapshotsPlugin(on, config);
      const {
        installPlugin: installMockApiPlugin,
      } = require("@swimlane/cy-mockapi/build/main/index");
      installMockApiPlugin(on, config);
      return config;
    },
  },
  component: {
    specPattern: "src/components/**/*.spec.tsx",
    supportFile: "cypress/support/component.ts",
    devServer: {
      framework: "react",
      bundler: "vite",
    },
    setupNodeEvents(on, config) {
      const getCompareSnapshotsPlugin = require("cypress-image-diff-js/plugin");
      getCompareSnapshotsPlugin(on, config);
      return config;
    },
  },
  env: {
    VIDEO: false,
    SNAPSHOT_TEST_THRESHOLD: 0.5,
  },
});
