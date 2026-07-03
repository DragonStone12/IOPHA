# Visual Regression Testing Best Practices Playbook
**For IOPHA Frontend (Cypress + cypress-image-diff-js + React/Vite/Tailwind CSS v4)**

## Table of Contents

| # | Section | Description |
|---|---------|-------------|
| 1 | [Overview](#overview) | Tech stack and scope |
| 2 | [Browser Launch Flags](#1-ensure-consistent-rendering-with-browser-launch-flags) | Normalize rendering across environments |
| 3 | [Dynamic Content](#2-normalize-dynamic-or-transient-content) | Handle timestamps, IDs, user-specific data |
| 4 | [Wait for Elements](#3-wait-for-all-visual-elements-before-snapshot) | Ensure fonts, images, SVGs load |
| 5 | [Scoped Snapshots](#4-keep-snapshots-isolated-and-scoped) | Target stable regions, not entire pages |
| 6 | [Component Snapshots](#5-component-level-snapshot-testing-in-spectsx) | Snapshot rules and naming conventions |
| 7 | [Snapshot Naming](#6-use-meaningful-snapshot-names) | Descriptive naming patterns |
| 8 | [Version Control](#7-commit-baseline-snapshots-to-source-control) | Track baselines in Git |
| 9 | [Review Diffs](#8-review-diffs-carefully--avoid-blind-updates) | Local update workflow |
| 10 | [CI Testing](#9-use-ci-for-visual-testing-with-fixed-environments) | Fixed viewport, artifact uploads |
| 11 | [Thresholds](#10-threshold-configuration) | Pixel tolerance settings |
| 12 | [Responsive Design](#11-responsive-design-testing) | Mobile and tablet viewports |
| 13 | [Third-Party Content](#12-handle-third-party-content) | Mock maps, ads, embeds |
| 14 | [Performance](#13-performance-considerations) | Optimize runtime and storage |
| 15 | [Flaky Tests](#14-handling-flaky-tests) | Stabilize animations and delayed rendering |
| 16 | [Maintenance](#15-maintenance-and-cleanup) | Prevent snapshot bloat |
| 17 | [Overflow Issues](#16-avoiding-overflow-related-baseline-failures) | Handle CSS overflow clipping |
| 18 | [Training Example](#17-training-example-fixing-a-visual-bug-overflow-issue) | Step-by-step overflow fix |
| 19 | [Quick Reference](#quick-reference-card) | Do/Don't cheat sheet |

## Overview
Visual regression testing guards against unintended UI changes, layout shifts, broken components, and styling regressions that functional tests miss. This guide is tailored for our Cypress setup with `cypress-image-diff-js` for visual comparison.

For E2E BDD testing, component testing, and the mandatory TDD workflow, see [`CYPRESS_TESTING.md`](./CYPRESS_TESTING.md).

**Tech stack:**
- Cypress 15
- `cypress-image-diff-js` — provides `cy.compareSnapshot()` for visual comparison
- `@swimlane/cy-mockapi` — API response mocking for consistent test data
- `start-server-and-test` — orchestrates dev server + Cypress in `test:e2e`
- Husky (monorepo root) — pre-push runs `lint + test:e2e + component tests + audit`

---

## 1. Ensure Consistent Rendering with Browser Launch Flags

Visual test failures often trace back to differences in screen resolution, scaling, or GPU rendering across environments. Normalize the rendering environment via browser flags in your Cypress configuration.

**Update `cypress.config.ts`:**
```typescript
export default defineConfig({
  e2e: {
    viewportWidth: 1440,
    viewportHeight: 900,
    setupNodeEvents(on, config) {
      on('before:browser:launch', (browser = {}, launchOptions) => {
        if (browser.name === 'chrome' || browser.name === 'chromium') {
          launchOptions.args.push('--force-device-scale-factor=1');
          launchOptions.args.push('--disable-gpu');
          launchOptions.args.push('--window-size=1440,900');
          launchOptions.args.push('--font-render-hinting=none');
        }
        return launchOptions;
      });
      // ... rest of your setup
    },
  },
});
```

**Note:** Use 1440x900 as the standard viewport. This matches typical desktop viewports and prevents content clipping that occurs at smaller sizes like 1280x720.

---

## 2. Normalize Dynamic or Transient Content

Dynamic values such as timestamps, random IDs, or user-specific data produce false-positive diffs. Before taking a snapshot, intercept, mock, or mutate any DOM content that varies between sessions.

**In your component tests or E2E tests:**
```typescript
// Remove dynamic timestamps
cy.get('.timestamp, .date').invoke('text', '[DATE]');

// Normalize user-specific content
cy.get('.user-name').invoke('text', 'Test User');

// Mock API responses for consistent data (using cy-mockapi)
// Configured in cypress/support/e2e.ts:
//   cy.mockApi({ apiPath: "/api/", mocksFolder: "mocks", cache: true });
```

---

## 3. Wait for All Visual Elements Before Snapshot

Snapshots taken before images, fonts, or SVGs finish loading produce inconsistent results. Assert that all critical visual components are present before capturing.

**Component test example:**
```typescript
it('should render the nutrition response correctly', () => {
  cy.mount(<NutritionResponse data={MOCK_DATA} />);

  // Wait for critical visual elements
  cy.contains('irregular meal timing').should('be.visible');
  cy.contains('Dr. Emily Chen, MD').should('be.visible');
  cy.get('svg').should('have.length.gt', 0);

  // Ensure fonts are loaded
  cy.get('body').should('have.css', 'font-family').and('not.be.empty');

  // Now take snapshot
  cy.compareSnapshot('nutrition-response-default');
});
```

---

## 4. Keep Snapshots Isolated and Scoped

**DO: Target scoped, stable regions within a component**
```typescript
// Snapshot a specific section of a mounted component
cy.get('aside').compareSnapshot('sidebar-default');
cy.get('[data-testid="physician-card"]').compareSnapshot('physician-card-default');
```

**DON'T: Snapshot the entire mounted component when only one section changed**
```typescript
// If you only changed the physician card, don't snapshot the whole NutritionResponse
// Instead, snapshot just the physician card section
```

**Use semantic selectors for stability:**
```tsx
// In your React components, use stable class names or element types
<aside className="w-80 shrink-0 bg-card border-r border-border">
```

**Component-level snapshots:** When testing a component in isolation with `cy.mount()`, the entire mounted component IS the scope. In this case, one snapshot per test is appropriate. The "scoped" rule applies when you have multiple distinct visual regions within a single mounted component that could change independently.

---

## 5. Component-Level Snapshot Testing in `*.spec.tsx`

Visual snapshots belong inside component test files (`*.spec.tsx`) alongside functional assertions. Every component that renders UI should have at least one `cy.compareSnapshot()` call in its spec file.

**Place `cy.compareSnapshot()` after your functional assertions in the same test:**

```typescript
// src/components/RiskProfileSidebar/RiskProfileSidebar.spec.tsx
import { RiskProfileSidebar } from './RiskProfileSidebar';

describe('RiskProfileSidebar Component', () => {
  it('should render user card with correct details', () => {
    cy.mount(
      <RiskProfileSidebar
        userName="Test User"
        userAge={28}
        userLocation="New York, NY"
      />,
    );
    cy.contains("Test User").should("be.visible");
    cy.contains("28 years").should("be.visible");
    cy.contains("New York, NY").should("be.visible");

    // Visual snapshot — captures the rendered UI for regression comparison
    cy.compareSnapshot("risk-profile-sidebar-default");
  });

  it('should display HIGH RISK badge when score > 70', () => {
    cy.mount(<RiskProfileSidebar riskScore={85} />);
    cy.contains("HIGH RISK").should("be.visible");
    cy.compareSnapshot("risk-profile-sidebar-high-risk");
  });
});
```

**Rules for component snapshots:**

1. **One snapshot per test** — each `it()` block that mounts a component should end with a `cy.compareSnapshot()` call.
2. **Snapshot after assertions** — place `cy.compareSnapshot()` after all `cy.contains()` / `cy.get()` assertions so the DOM is fully rendered.
3. **Descriptive names** — use `<component-name>-<state>` format: `nutrition-response-default`, `chat-area-with-greeting`, `sidebar-high-risk`.
4. **Generate baselines locally first** — run `npm run cy:update-snapshots:spec "src/components/MyComponent/MyComponent.spec.tsx"` to create the baseline PNG before the test can pass.
5. **Commit baselines to Git** — baseline PNGs live in `cypress-visual-screenshots/baseline/` and must be tracked in version control.

**Current component snapshot coverage:**

| Component | Spec File | Snapshot Name |
|-----------|-----------|---------------|
| LandingPage | `LandingPage/LandingPage.spec.tsx` | `landing-page-default` |
| RiskProfileSidebar | `RiskProfileSidebar/RiskProfileSidebar.spec.tsx` | `risk-profile-sidebar-default` |
| ChatArea | `ChatArea/ChatArea.spec.tsx` | `chat-area-default` |
| NutritionResponse | `NutritionResponse/NutritionResponse.spec.tsx` | `nutrition-response-default` |

**When adding a new component:**

1. Create `src/components/MyComponent/MyComponent.spec.tsx`
2. Write functional tests with `cy.mount()` and `cy.contains()`
3. Add `cy.compareSnapshot("my-component-default")` at the end of each test
4. Generate the baseline: `npm run cy:update-snapshots:spec "src/components/MyComponent/MyComponent.spec.tsx"`
5. Commit the spec file and the generated baseline PNG together

---

## 6. Use Meaningful Snapshot Names

Vague names make debugging difficult. Use descriptive names that reflect the UI area and state.

**Good naming convention:**
```typescript
cy.compareSnapshot('landing-page-default');
cy.compareSnapshot('sidebar-high-risk');
cy.compareSnapshot('chat-area-with-greeting');
cy.compareSnapshot('nutrition-response-default');
```

**Bad naming convention:**
```typescript
cy.compareSnapshot('test1');
cy.compareSnapshot('screenshot');
cy.compareSnapshot('default');
```

---

## 7. Baseline Storage and Version Control

Visual regression baselines are generated locally and are **not committed to Git**. They do not represent test fixtures; they are cached artifacts from the last local snapshot update.

**Baseline location:**
```text
IOPHA-frontend/cypress-visual-screenshots/baseline/
```

**Diff output location:**
```text
IOPHA-frontend/cypress-visual-screenshots/diff/
IOPHA-frontend/cypress-visual-screenshots/comparison/
```

**Report location:**
```text
IOPHA-frontend/cypress-visual-report/
```

Add these directories to `.gitignore` so local baselines are not accidentally committed. The goal is simply to locally verify that visual diffs are intentional, not to preserve a historical baseline in source control.

---

## 8. Review Diffs Carefully — Avoid Blind Updates

### Updating Baselines Locally (Recommended)

Always update baselines locally first so you can visually verify the changes before committing them.

**npm scripts for snapshot updates** (from `package.json`):
```json
{
  "scripts": {
    "test:e2e": "start-server-and-test dev http://localhost:3000 cy:run",
    "cy:update-snapshots": "start-server-and-test dev http://localhost:3000 cy:update-snapshots:core",
    "cy:update-snapshots:core": "cypress run --env updateSnapshots=true",
    "cy:update-snapshots:spec": "start-server-and-test dev http://localhost:3000 'cypress run --env updateSnapshots=true --spec'",
    "cy:clean-diffs": "find cypress-visual-screenshots/diff -type f -name '*.png' -delete"
  }
}
```

**What each script does:**
- `test:e2e` — Starts Vite dev server and runs all Cypress E2E tests (Gherkin BDD feature files)
- `cy:update-snapshots` — Starts dev server, runs all tests, updates visual baselines
- `cy:update-snapshots:core` — Runs Cypress with `updateSnapshots=true` (expects server already running)
- `cy:update-snapshots:spec` — Starts server and updates baselines for a specific spec file
- `cy:clean-diffs` — Deletes diff PNGs from `cypress-visual-screenshots/diff/`

**Usage:**
```bash
# Update all visual baselines
npm run cy:update-snapshots

# Update baseline for a specific component test
npm run cy:update-snapshots:spec "src/components/NutritionResponse/NutritionResponse.spec.tsx"

# Update baseline for a specific E2E feature test
npm run cy:update-snapshots:spec "cypress/e2e/Tests/nutrition-tips.feature"
```

### Baseline Scope

Visual diffs are only local-dev artifacts. Baseline PNGs in `cypress-visual-screenshots/baseline/` are regenerated on every local snapshot update and are not committed to Git.

If update is intentional:
1. Review the diff image in `cypress-visual-screenshots/diff/`
2. Run with update flag locally: `npm run cy:update-snapshots`
3. Do not commit the regenerated baselines
   ```

---

## 9. Use CI for Visual Testing with Fixed Environments

The Husky pre-push hook runs tests before every push, providing a consistent local environment. In CI, ensure the same viewport and browser settings are used.

**Upload diff artifacts on failure** (add to your CI workflow):
```yaml
- name: Upload visual diffs
  uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: visual-diffs
    path: |
      IOPHA-frontend/cypress-visual-screenshots/diff/
      IOPHA-frontend/cypress-visual-screenshots/comparison/
      IOPHA-frontend/cypress/screenshots/
    if-no-files-found: ignore
```

---

## 10. Threshold Configuration

`cypress-image-diff-js` uses pixel-by-pixel comparison. The default threshold is 0 (any difference fails). You can configure this in the plugin setup.

**In `cypress.config.ts`:**
```typescript
const getCompareSnapshotsPlugin = require("cypress-image-diff-js/plugin");

getCompareSnapshotsPlugin(on, config, {
  // Optional: set a small tolerance for antialiasing differences
  // errorThreshold: 0.01, // 1% tolerance
});
```

**In `cypress-image-diff.config.cjs`:**
```javascript
module.exports = {
  SCREENSHOTS_DIR: "cypress-visual-screenshots",
  REPORT_DIR: "cypress-visual-report",
};
```

---

## 11. Responsive Design Testing

Test across multiple viewport sizes to catch responsive regressions.

**In your component tests:**
```typescript
it('should render correctly on mobile', () => {
  cy.viewport(375, 667);
  cy.mount(<LandingPage />);
  cy.contains('Health Assistant').should('be.visible');
  cy.compareSnapshot('landing-page-mobile-375x667');
});

it('should render correctly on tablet', () => {
  cy.viewport(768, 1024);
  cy.mount(<LandingPage />);
  cy.compareSnapshot('landing-page-tablet-768x1024');
});
```

---

## 12. Handle Third-Party Content

Uncontrolled third-party content (maps, ads, embeds) produces inconsistent diffs. Mock or remove them before snapshotting.

```typescript
// Block external requests
cy.intercept('https://maps.googleapis.com/**', {
  statusCode: 204
});

// Remove third-party widgets
cy.get('#analytics-widget').invoke('remove');
```

---

## 13. Performance Considerations

Visual tests add runtime and storage overhead.

**Optimizations:**
1. **Scope snapshots** to key regions when possible, not full components
2. **Use `.only()` locally** during development:
   ```typescript
   it.only('should render the landing page', () => { ... });
   ```
3. **Run full suite in CI** via Husky pre-push hook and GitHub Actions
4. **Clean up old diffs regularly:**
   ```bash
   npm run cy:clean-diffs
   ```

---

## 14. Handling Flaky Tests

Common causes: animations, delayed rendering, third-party content.

**Stabilization techniques:**
```typescript
// Disable CSS transitions
cy.document().then((doc) => {
  const style = doc.createElement('style');
  style.innerHTML = '* { transition: none !important; animation: none !important; }';
  doc.head.appendChild(style);
});

// Wait for network idle using cy-mockapi
// Mocked in cypress/support/e2e.ts beforeEach:
//   cy.mockApi({ apiPath: "/api/", mocksFolder: "mocks", cache: true });

// Assert visibility before snapshot
cy.contains('Health Assistant')
  .should('be.visible')
  .then(() => {
    cy.compareSnapshot('landing-page-default');
  });
```

---

## 15. Maintenance and Cleanup

**Prevent snapshot bloat:**
1. **Remove orphaned snapshots** when components are deleted
2. **Document major visual changes** in PR descriptions
3. **Clean diff output regularly:**
   ```bash
   npm run cy:clean-diffs
   ```

---

## 16. Avoiding Overflow-Related Baseline Failures

Layout changes that introduce or remove `overflow` CSS properties are a common cause of visual regression baseline failures. When a parent container has `overflow-hidden` or `overflow-y-auto`, child content that exceeds the container bounds gets clipped. This causes two problems:

1. **Functional test failures**: `cy.contains().should("be.visible")` fails because elements are clipped
2. **Visual regression failures**: The baseline image shows clipped content, but after layout changes the content may no longer be clipped (or vice versa), causing diff mismatches

### Root Causes

| Cause | Symptom | Fix |
|-------|---------|-----|
| Parent has `overflow-hidden` | Content clipped at container edge | Remove `overflow-hidden` if content should be visible |
| Sidebar has `overflow-y-auto` | Bottom items clipped in small viewports | Remove overflow or ensure content fits |
| Cypress viewport too small | Content overflows in headless mode | Increase viewport size in `cypress.config.ts` |

### Best Practices

**1. Avoid `overflow-hidden` on layout containers unless necessary**

```tsx
// AVOID: Clips sidebar content when viewport is small
<div className="flex flex-1 w-full overflow-hidden">

// PREFER: Let content flow naturally
<div className="flex flex-1 w-full">
```

If you need overflow control for a specific reason (e.g., preventing horizontal scroll), apply it to the specific element that needs it, not the entire layout container.

**2. Don't add `overflow-y-auto` to sidebars unless content genuinely overflows**

```tsx
// AVOID: Clips bottom nav items in small viewports
<aside className="w-80 flex flex-col overflow-y-auto">

// PREFER: Only add overflow if content is genuinely scrollable
<aside className="w-80 flex flex-col">
```

**3. Set an appropriate viewport size in Cypress config**

```typescript
// cypress.config.ts
export default defineConfig({
  e2e: {
    viewportWidth: 1440,
    viewportHeight: 900,
    // ...
  },
});
```

**4. Use `scrollIntoView()` for intentionally scrollable containers**

If a container is meant to be scrollable, scroll elements into view before asserting:

```typescript
cy.contains("Bottom nav item").scrollIntoView().should("be.visible");
```

### When Baselines Fail After Layout Changes

If visual regression baselines fail after you change overflow/layout CSS:

1. **Review the diff carefully** — confirm the change is intentional
2. **Update the baseline locally** using the proper workflow:
   ```bash
   npm run cy:update-snapshots:spec "src/components/RiskProfileSidebar/RiskProfileSidebar.spec.tsx"
   ```
3. **Commit the updated baseline** with a descriptive message:
   ```bash
   git add cypress-visual-screenshots/baseline/
   git commit -m "chore: update visual baseline after removing overflow-hidden from layout [snap-update]"
   ```

**Never blindly update baselines in CI.** Always review diffs locally first.

---

## 17. Training Example: Fixing a Visual Bug (Overflow Issue)

**Before:**
```typescript
// Test fails: "Sleep & recovery button not visible"
cy.contains('Sleep & recovery').should('be.visible');
```

**Diagnosis:**
```bash
# Check screenshot
open cypress/screenshots/RiskProfileSidebar.spec.tsx/failure.png
# Found: parent has overflow-y-auto causing clipping
```

**Fix:**
```tsx
// BEFORE:
<aside className="w-80 overflow-y-auto">

// AFTER:
<aside className="w-80">  {/* Removed overflow-y-auto */}
```

**Update Baseline:**
```bash
npm run cy:update-snapshots:spec "src/components/RiskProfileSidebar/RiskProfileSidebar.spec.tsx"
git commit -m "fix: sidebar overflow clipping bug - Updated visual baseline"
```

---

## Quick Reference Card

| **Do** | **Don't** |
|--------|-----------|
| Use `cy.compareSnapshot()` | Use `cy.matchImageSnapshot()` (wrong library) |
| Wait for elements to load | Use `cy.wait()` arbitrarily |
| Scope to stable regions | Blindly update snapshots |
| Use meaningful snapshot names | Ignore diff reviews |
| Run tests via Husky pre-push hook | Run visual tests locally only |
| Commit baselines to Git | Store snapshots only locally |
| Mock dynamic content via `cy-mockapi` | Test with live unpredictable data |
| Use `--env updateSnapshots=true` | Use `UPDATE_SNAPSHOTS=true` (wrong env var) |
| Use 1440x900 viewport | Use small viewports that cause clipping |

---

## Next Steps

1. **Add responsive viewport tests** to critical components (mobile, tablet)
2. **Add snapshot tests** to any new components created
3. **Review and update baselines** when making intentional UI changes
4. **Monitor CI artifact uploads** for visual diff debugging

---

**Remember:** Visual regression testing is about catching unintended changes, not preventing intentional ones. Review every diff, understand every failure, and update baselines deliberately.
