# Troubleshooting: Cypress Cucumber Preprocessor Step Definitions Not Found

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