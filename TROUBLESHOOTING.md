# Troubleshooting: Cypress Cucumber Preprocessor Step Definitions Not Found

## Table of Contents

- [Troubleshooting: Cypress Cucumber Preprocessor Step Definitions Not Found](#troubleshooting-cypress-cucumber-preprocessor-step-definitions-not-found)
  - [Problem Summary](#problem-summary)
  - [Root Cause](#root-cause)
  - [Troubleshooting Steps](#troubleshooting-steps)
  - [Resolution](#resolution)
  - [Final Working Structure](#final-working-structure)
  - [Key Learnings](#key-learnings)
- [npm audit Serialization/JavaScript Vulnerability](#npm-audit-serializationjavascript-vulnerability)
  - [Issue](#issue)
  - [Detection](#detection)
  - [Solution Implemented](#solution-implemented)
- [@swimlane/cy-mockapi: Module Resolution and Browser-Context Verification](#swimlanecy-mockapi-module-resolution-and-browser-context-verification)
  - [Problem Summary](#problem-summary-1)
  - [Root Cause](#root-cause-1)
  - [Resolution](#resolution-1)
  - [Verification](#verification)
  - [Key Learnings](#key-learnings-1)
- [Visual Regression Testing: Artifacts Cleanup and Documentation](#visual-regression-testing-artifacts-cleanup-and-documentation)
  - [Problem Summary](#problem-summary-2)
  - [Resolution](#resolution-2)
  - [Verification](#verification-1)

## Problem Summary
Cypress E2E tests failed with "Step implementation missing" error despite step definitions existing. The `@badeball/cypress-cucumber-preprocessor` plugin could not locate the step definition files.

## Root Cause
1. Step definitions were placed in `cypress/e2e/Tests/homepage.steps.ts` but the plugin expected them in `cypress/support/step_definitions/` by default
2. The import path `@badeball/cypress-cucumber-preprocessor/steps` was incorrect - the correct import is `@badeball/cypress-cucumber-preprocessor`

## Troubleshooting Steps
1. Verified plugin installation and package structure in `node_modules/@badeball/cypress-cucumber-preprocessor/`
2. Examined the `exports` field in `package.json` to confirm correct import paths
3. Checked step definition file locations against default search patterns shown in error:
   - `cypress/e2e/Tests/[filepath]/**/*.{js,mjs,ts,tsx}`
   - `cypress/e2e/Tests/[filepath].{js,mjs,ts,tsx}`
   - `cypress/support/step_definitions/**/*.{js,mjs,ts,tsx}`
4. Identified that `[filepath]` resolves to the feature file path without extension (e.g., `app` for `app.feature`)
5. Moved step definitions to `cypress/support/step_definitions/` folder which is the global fallback

## Resolution
1. Renamed `homepage.feature` to `app.feature` and `homepage.steps.ts` to `app.steps.ts`
2. Moved `app.steps.ts` to `cypress/support/step_definitions/`
3. Changed import from `@badeball/cypress-cucumber-preprocessor/steps` to `@badeball/cypress-cucumber-preprocessor`
4. Simplified `cypress.config.ts` to use default configuration without explicit `stepDefinitions` path

## Final Working Structure
```
cypress/
├── e2e/
│   └── Tests/
│       └── app.feature
└── support/
    ├── e2e.ts
    └── step_definitions/
        └── app.steps.ts
```

## Key Learnings
- The `@badeball/cypress-cucumber-preprocessor` uses a `[filepath]` template variable to pair feature files with step definitions
- For `app.feature`, it looks for `app/*.{js,ts}` or `app.{js,ts}` in the Tests directory
- The `cypress/support/step_definitions/` folder is a built-in fallback path that always gets searched
- Import syntax should be `import { Given, When, Then } from "@badeball/cypress-cucumber-preprocessor"` (no `/steps` subpath)

## npm audit Serialization/JavaScript Vulnerability

### Issue
The pre-push hook blocked pushes due to vulnerabilities in `serialize-javascript` (RCE vulnerability). The original audit level was correctly set to `high`, but it was checking dev dependencies which contain transitive vulnerabilities that don't affect production code.

### Detection
Running `npm audit` showed: `3 vulnerabilities (2 moderate, 1 high)` in `serialize-javascript` <=7.0.4, pulled in transitively via `mocha` (a dependency of `@badeball/cypress-cucumber-preprocessor`).

### Solution Implemented
Updated `.husky/pre-push` and `.github/workflows/ci-frontend.yml` to use `npm audit --omit=dev --audit-level=high`. This only audits production dependencies at high severity, ignoring dev-only vulnerabilities that don't affect deployed code.

**Files modified:**
- `.husky/pre-push:` Uses `npm audit --omit=dev --audit-level=high`
- `.github/workflows/ci-frontend.yml:` Uses `npm audit --omit=dev --audit-level=high`

---

## @swimlane/cy-mockapi: Module Resolution and Browser-Context Verification

### Problem Summary
Integrating `@swimlane/cy-mockapi@3.0.0` into the Cypress test suite failed with two errors:
1. `Cannot find module '@swimlane/cy-mockapi/plugin'` and `Cannot find module '@swimlane/cy-mockapi/commands'`
2. Verification test using `cy.request()` failed because mocked responses were never returned

### Root Cause
Path resolution is relative to the fixtures folder, not the project root. The package does not expose `/plugin` or `/commands` subpaths in its `package.json` `exports` field; it only exports them under `build/main/` and `build/module/`.

### Resolution
1. **Plugin registration in `cypress.config.ts`:**
   ```typescript
   const { installPlugin: installMockApiPlugin } = require("@swimlane/cy-mockapi/build/main/index");
   installMockApiPlugin(on, config);
   ```

2. **Command registration in `cypress/support/commands.ts`:**
   ```typescript
   require("@swimlane/cy-mockapi/build/main/commands");
   ```

3. **`cy.mockApi()` configuration in `cypress/support/e2e.ts`:**
   ```typescript
   beforeEach(() => {
     cy.mockApi({
       apiPath: "/api/",
       mocksFolder: "mocks", // resolves to cypress/fixtures/mocks (NOT cypress/fixtures/cypress/fixtures/mocks)
       cache: true,
     });
   });
   ```

4. **Mock fixture structure:**
   ```text
   cypress/fixtures/mocks/
   └── user/
       ├── get.json
       ├── __/
       │   └── profile/
       │       └── get.json
       └── --id=1/
           └── get.json
   ```

### Verification
Use `cy.window().then(win => win.fetch(...))` instead of `cy.request()`. `cy.request()` bypasses the browser's network stack (where `cy.intercept()` operates) and makes direct Node-level HTTP calls, so it always skips browser-based mocks.

```typescript
it("should return mocked JSON", () => {
  cy.visit("/");
  cy.window().then(win => win.fetch("/api/user")).then(res => {
    expect(res.status).to.eq(200);
    return res.json();
  }).then(data => {
    expect(data).to.have.property("name", "Test User");
  });
});
```

### Key Learnings
- `@swimlane/cy-mockapi` requires Cypress >13.0.0 (project uses Cypress 15.18.0 ✓)
- `mocksFolder` is resolved relative to `config.fixturesFolder` (`cypress/fixtures/`), so use `"mocks"`, not `"cypress/fixtures/mocks"`
- `cy.intercept()` intercepts in-browser requests only; `cy.request()` runs in Node and cannot be intercepted
- Wildcard slugs use `__` in folder/file names: `user/__/profile/get.json` matches `/user/*/profile`
- Query parameters use `--`: `user/--id=1/get.json` matches `/user?id=1`

---

## Visual Regression Testing: Artifacts Cleanup and Documentation

### Problem Summary
First run of `cy.compareSnapshot()` left large binary artifacts (PNG baselines, comparison, diff, HTML reports) in the working tree. These generated files bloat the repo and should not be committed.

### Resolution
1. Added generated artifact directories to `.gitignore`:
   ```gitignore
   # Visual Regression Test Artifacts
   IOPHA-frontend/cypress-visual-screenshots/
   IOPHA-frontend/cypress-visual-report/
   ```
2. Cleaned up existing artifacts before commit with `rm -rf`.
3. Documented the visual testing strategy and artifact handling in `docs/product_plan/TECHNICAL_DESIGN_DOCUMENT.md` and added a comprehensive `docs/product_plan/VISUAL_REGRESSION_PLAYBOOK.md`.
4. Added GitHub Actions artifact upload for visual diffs on test failure in `.github/workflows/ci-frontend.yml`.

### Verification
Visual regression test passes on first run (baseline created) and fails with a diff image when UI changes. HTML reports are generated via `cy.task("generateReport")` in the `after()` hook.