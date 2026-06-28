# Visual Regression Testing Best Practices Playbook
**For IOPHA Frontend (Cypress + cypress-image-diff-js + React/Vite/Tailwind CSS v4)**

## Overview
Visual regression testing guards against unintended UI changes, layout shifts, broken components, and styling regressions that functional tests miss. This guide is tailored for our Cypress setup with `cypress-image-diff-js` for visual comparison.

**Tech stack:**
- Cypress 15 (E2E + Component Testing via `cy.mount`)
- `cypress-image-diff-js` — provides `cy.compareSnapshot()` for visual comparison
- `@badeball/cypress-cucumber-preprocessor` — BDD `.feature` files for E2E
- `@swimlane/cy-mockapi` — API response mocking
- `start-server-and-test` — orchestrates dev server + Cypress in `test:e2e`
- Husky (monorepo root) — pre-push runs `lint + test:e2e + audit`

---

## Testing Strategy: E2E vs Component Tests

### E2E Tests (Gherkin BDD)

E2E tests use **Gherkin syntax** (`.feature` files) located in `cypress/e2e/Tests/`. These tests visit the actual application and verify user flows end-to-end.

**File structure:**
```
cypress/e2e/
└── Tests/
    └── app.feature          # Gherkin feature files (E2E tests ONLY)
```

All E2E tests use Gherkin syntax in `.feature` files. Step definitions are in `cypress/support/step_definitions/`.

**Gherkin feature file example** (`cypress/e2e/Tests/app.feature`):
```gherkin
Feature: Landing Page
  Scenario: User views the landing page
    Given I am on the landing page
    When I view the page
    Then I should see the title "Health Assistant"
```

**Step definitions** (`cypress/support/step_definitions/app.steps.ts`):
```typescript
import { Given, When, Then } from "@badeball/cypress-cucumber-preprocessor";

Given("I am on the landing page", () => {
  cy.visit("/");
});

When("I view the page", () => {
  cy.contains("Health Assistant").should("be.visible");
});

Then("I should see the title {string}", (expectedTitle: string) => {
  cy.contains(expectedTitle).should("be.visible");
});
```

**When to use E2E tests:**
- Full page layouts and user flows
- Multi-component interactions
- End-to-end user journeys
- Visual regression snapshots of complete pages

### Component Tests (`.spec.tsx`)

Component tests use **Cypress Component Testing** with `cy.mount()` to test components in isolation. Test files use `.spec.tsx` extension and live alongside components in `src/components/`.

**File structure:**
```
src/components/
├── LandingPage/
│   ├── LandingPage.tsx
│   └── LandingPage.spec.tsx    # Component test
├── RiskProfileSidebar/
│   ├── RiskProfileSidebar.tsx
│   └── RiskProfileSidebar.spec.tsx
└── ChatArea/
    ├── ChatArea.tsx
    └── ChatArea.spec.tsx
```

**Component test example** (`src/components/RiskProfileSidebar/RiskProfileSidebar.spec.tsx`):
```typescript
import { RiskProfileSidebar } from "./RiskProfileSidebar";

describe("RiskProfileSidebar Component", () => {
  it("should render user card with correct details", () => {
    cy.mount(
      <RiskProfileSidebar
        userName="Test User"
        userAge={28}
        userLocation="New York, NY"
      />
    );
    cy.contains("Test User").should("be.visible");
    cy.contains("28 years").should("be.visible");
  });

  it("should display HIGH RISK badge when score > 70", () => {
    cy.mount(<RiskProfileSidebar riskScore={85} />);
    cy.contains("HIGH RISK").should("be.visible");
  });
});
```

**When to use component tests:**
- Discrete UI states (hover, active, disabled)
- Isolated component validation
- Props and event handling
- Faster feedback during development

---

## Cypress Component Testing Guide

### Setup

Component testing is configured in `cypress.config.ts` under the `component` key:

```typescript
component: {
  specPattern: "src/components/**/*.spec.tsx",
  supportFile: "cypress/support/component.ts",
  devServer: {
    framework: "react",
    bundler: "vite",
  },
}
```

**Support file** (`cypress/support/component.ts`):
```typescript
import { mount } from "cypress/react18";
import "../../src/index.css";

declare global {
  namespace Cypress {
    interface Chainable {
      mount: typeof mount;
    }
  }
}

Cypress.Commands.add("mount", mount);
```

### Mounting Components

**Basic mount:**
```typescript
cy.mount(<Button>Click me</Button>);
cy.get("button").should("be.visible");
```

**Mount with props:**
```typescript
cy.mount(
  <Card
    title="Welcome"
    description="Test card"
    variant="primary"
  />
);
cy.contains("Welcome").should("be.visible");
```

**Mount with providers/context:**
```typescript
cy.mount(
  <QueryProvider>
    <LandingPage userName="Sarah Mitchell" riskScore={78} />
  </QueryProvider>
);
```

### Testing Props and Events

**Testing props:**
```typescript
it("renders different risk levels", () => {
  cy.mount(<RiskProfileSidebar riskScore={85} />);
  cy.contains("HIGH RISK").should("be.visible");

  cy.mount(<RiskProfileSidebar riskScore={50} />);
  cy.contains("MODERATE RISK").should("be.visible");
});
```

**Testing callbacks with stubs:**
```typescript
it("fires onTopicSelect callback when chip is clicked", () => {
  const callback = cy.stub().as("topicSelect");
  cy.mount(<ChatArea onTopicSelect={callback} />);
  cy.contains("Find a doctor").click();
  cy.get("@topicSelect").should("have.been.calledWith", "find_a_doctor");
});
```

### Stubbing Dependencies

**Stubbing HTTP requests:**
```typescript
cy.intercept("GET", "/api/users", {
  statusCode: 200,
  body: [{ id: 1, name: "Alice" }],
}).as("getUsers");

cy.mount(<UserList />);
cy.wait("@getUsers");
cy.contains("Alice").should("be.visible");
```

### Visual Testing

**Snapshot testing with cypress-image-diff-js:**
```typescript
it("matches snapshot for default state", () => {
  cy.mount(<RiskProfileSidebar />);
  cy.compareSnapshot("risk-profile-sidebar-default");
});

it("matches snapshot for high risk", () => {
  cy.mount(<RiskProfileSidebar riskScore={85} />);
  cy.compareSnapshot("risk-profile-sidebar-high-risk");
});
```

### Best Practices

**Test organization:**
```typescript
describe("LoginForm", () => {
  describe("validation", () => {
    it("shows error for invalid email");
    it("shows error for short password");
  });

  describe("submission", () => {
    it("submits valid credentials");
    it("shows error on failed login");
  });
});
```

**Keep tests independent:**
```typescript
beforeEach(() => {
  // Reset state before each test
  cy.intercept("GET", "/api/cart", { items: [] });
});
```

**Use semantic selectors:**
```typescript
// Good - stable selectors
cy.contains("Sleep & recovery").should("be.visible");
cy.get('input[placeholder*="Ask about"]').should("be.visible");

// Avoid - fragile selectors
cy.get(".btn-primary").click();
cy.get("button").first().click();
```

---

## 1. Ensure Consistent Rendering with Browser Launch Flags

Visual test failures often trace back to differences in screen resolution, scaling, or GPU rendering across environments. Normalize the rendering environment via browser flags in your Cypress configuration.

**Update `cypress.config.ts`:**
```typescript
export default defineConfig({
  e2e: {
    viewportWidth: 1280,
    viewportHeight: 720,
    setupNodeEvents(on, config) {
      on('before:browser:launch', (browser = {}, launchOptions) => {
        if (browser.name === 'chrome' || browser.name === 'chromium') {
          launchOptions.args.push('--force-device-scale-factor=1');
          launchOptions.args.push('--disable-gpu');
          launchOptions.args.push('--window-size=1280,720');
          launchOptions.args.push('--font-render-hinting=none');
        }
        return launchOptions;
      });
      // ... rest of your setup
    },
  },
});
```

---

## 2. Normalize Dynamic or Transient Content

Dynamic values such as timestamps, random IDs, or user-specific data produce false-positive diffs. Before taking a snapshot, intercept, mock, or mutate any DOM content that varies between sessions.

**In your Cucumber step definitions or E2E tests:**
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

**E2E test example:**
```typescript
it('should render the landing page correctly', () => {
  cy.visit('/');

  // Wait for critical visual elements
  cy.contains('Health Assistant').should('be.visible');
  cy.contains('Sarah Mitchell').should('be.visible');
  cy.get('svg').should('have.length.gt', 0);

  // Ensure fonts are loaded
  cy.get('body').should('have.css', 'font-family').and('not.be.empty');

  // Now take snapshot
  cy.compareSnapshot('landing-page');
});
```

---

## 4. Keep Snapshots Isolated and Scoped

**DO: Target scoped, stable regions**
```typescript
cy.get('aside').compareSnapshot('sidebar-default');
cy.get('main').compareSnapshot('chat-area-default');
```

**DON'T: Full-page snapshots when only one section changed**
```typescript
// Avoid this if you only changed the sidebar — too many moving parts
cy.compareSnapshot('full-page');
```

**Use semantic selectors for stability:**
```tsx
// In your React components, use stable class names or element types
<aside className="w-80 shrink-0 bg-card border-r border-border">
```

---

## 5. Use Meaningful Snapshot Names

Vague names make debugging difficult. Use descriptive names that reflect the UI area and state.

**Good naming convention:**
```typescript
cy.compareSnapshot('landing-page');
cy.compareSnapshot('sidebar-high-risk');
cy.compareSnapshot('chat-area-with-greeting');
```

---

## 6. Commit Baseline Snapshots to Source Control

Track snapshot PNG files in version control to maintain historical traceability and make visual changes reviewable in pull requests.

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

---

## 7. Review Diffs Carefully — Avoid Blind Updates

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
- `test:e2e` — Starts Vite dev server and runs all Cypress E2E tests
- `cy:update-snapshots` — Starts dev server, runs all tests, updates visual baselines
- `cy:update-snapshots:core` — Runs Cypress with `updateSnapshots=true` (expects server already running)
- `cy:update-snapshots:spec` — Starts server and updates baselines for a specific spec file
- `cy:clean-diffs` — Deletes diff PNGs from `cypress-visual-screenshots/diff/`

**Usage:**
```bash
# Update all visual baselines
npm run cy:update-snapshots

# Update baseline for a specific spec file only
npm run cy:update-snapshots:spec "cypress/e2e/visual-regression.cy.ts"
```

### Commit Updated Baselines

Once the command finishes, commit the updated baselines:
```bash
git add cypress-visual-screenshots/baseline/
git commit -m "chore: update visual baselines for sidebar redesign [snap-update]"
```

### Why You Should NOT Update Baselines in CI

If you update baselines in CI, you are blindly accepting whatever the UI looks like at that exact moment, which completely defeats the purpose of visual regression testing. If a developer accidentally pushes a broken UI, the CI will silently update the baseline to the broken state.

**NEVER commit `updateSnapshots=true` in CI workflows.** Treat snapshot failures as signals to investigate, not inconveniences to dismiss.

**Husky pre-push hook** (at monorepo root `.husky/pre-push`) already runs `test:e2e` before every push, catching visual regressions locally before they reach CI:
```bash
cd IOPHA-frontend && npm run lint && npm run test:e2e && npm audit --omit=dev --audit-level=high
```

**If update is intentional:**
1. Review the diff image in `cypress-visual-screenshots/diff/`
2. Run with update flag locally: `npm run cy:update-snapshots`
3. Commit snapshots in a separate commit with message:
   ```bash
   git commit -m "chore: update visual snapshots after sidebar redesign [snap-update]"
   ```

---

## 8. Use CI for Visual Testing with Fixed Environments

The Husky pre-push hook runs `test:e2e` before every push, providing a consistent local environment. In CI, ensure the same viewport and browser settings are used.

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

## 9. Threshold Configuration

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

## 10. Responsive Design Testing

Test across multiple viewport sizes to catch responsive regressions.

**In your E2E tests:**
```typescript
it('should render correctly on mobile', () => {
  cy.viewport(375, 667);
  cy.visit('/');
  cy.contains('Health Assistant').should('be.visible');
  cy.compareSnapshot('landing-page-mobile-375x667');
});

it('should render correctly on tablet', () => {
  cy.viewport(768, 1024);
  cy.visit('/');
  cy.compareSnapshot('landing-page-tablet-768x1024');
});
```

---

## 11. Handle Third-Party Content

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

## 12. Component-Level vs Integration Testing

**Use component tests** (Cypress Component Testing via `cy.mount`) for:
- Discrete UI states: Button hover, Card layout, Form validation
- Isolated validation without full page context
- Faster feedback during development

Component test files use `.spec.tsx` extension and live alongside components:
```typescript
// src/components/RiskProfileSidebar/RiskProfileSidebar.spec.tsx
import { RiskProfileSidebar } from './RiskProfileSidebar';

describe('RiskProfileSidebar', () => {
  it('renders user info', () => {
    cy.mount(<RiskProfileSidebar userName="John Doe" userAge={30} userLocation="NYC" />);
    cy.contains('John Doe').should('be.visible');
    cy.contains('30 years').should('be.visible');
  });

  it('displays risk score', () => {
    cy.mount(<RiskProfileSidebar riskScore={78} />);
    cy.get('[data-slot="progress-indicator"]').should('have.css', 'width');
  });
});
```

**Use E2E tests** (Cucumber `.feature` files + `.cy.ts` specs) for:
- Full page layouts
- Multi-component interactions
- End-to-end user flows

---

## 13. Performance Considerations

Visual tests add runtime and storage overhead.

**Optimizations:**
1. **Scope snapshots** to key regions, not full pages
2. **Use `.only()` locally** during development:
   ```typescript
   it.only('should render the landing page', () => { ... });
   ```
3. **Run full suite in CI** via Husky pre-push hook
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
    cy.compareSnapshot('landing-page');
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
| Placeholder text assertion | `cy.contains()` can't find placeholder | Use `cy.get('input[placeholder*="..."]')` |

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

**5. Use attribute selectors for placeholder text**

```typescript
// WRONG: cy.contains() looks for visible text nodes
cy.contains("Search...").should("be.visible");

// CORRECT: Check the placeholder attribute
cy.get('input[placeholder*="Search"]').should("be.visible");
```

### When Baselines Fail After Layout Changes

If visual regression baselines fail after you change overflow/layout CSS:

1. **Review the diff carefully** — confirm the change is intentional
2. **Update the baseline locally** using the proper workflow:
   ```bash
   npm run cy:update-snapshots:spec "cypress/e2e/visual-regression.cy.ts"
   ```
3. **Commit the updated baseline** with a descriptive message:
   ```bash
   git add cypress-visual-screenshots/baseline/
   git commit -m "chore: update visual baseline after removing overflow-hidden from layout [snap-update]"
   ```

**Never blindly update baselines in CI.** Always review diffs locally first.

---

## 17. Component-Driven Visual Testing Workflow (TDD Approach)

Build components **with tests from the start**, updating visual baselines incrementally as each component is developed. This ensures tests always reflect the current design intent.

### The TDD Cycle for Visual Components

```
Write Test → Run (Fails) → Write Minimal Component → Generate Baseline → Iterate
```

**Step 1: Write the component test first**
```typescript
// src/components/RiskProfileSidebar/RiskProfileSidebar.spec.tsx
import { RiskProfileSidebar } from './RiskProfileSidebar';

describe('RiskProfileSidebar Component', () => {
  it('should render risk profile sidebar', () => {
    cy.mount(<RiskProfileSidebar />);
    cy.contains('Sarah Mitchell').should('be.visible');
  });
});
```

**Step 2: Run test (it fails)**
```bash
# Component tests are configured in cypress.config.ts under the "component" key
# Spec pattern: src/components/**/*.spec.tsx
npx cypress run --component --spec "src/components/RiskProfileSidebar/RiskProfileSidebar.spec.tsx"
# Expected: Test fails because component doesn't exist yet
```

**Step 3: Create minimal component**
```tsx
export function RiskProfileSidebar() {
  return (
    <aside className="w-80 bg-card border-r">
      <div>User: Sarah Mitchell</div>
    </aside>
  );
}
```

**Step 4: Run test again — it passes**

**Step 5: Add visual snapshot and generate baseline**
```typescript
it('should render risk profile sidebar', () => {
  cy.mount(<RiskProfileSidebar />);
  cy.contains('Sarah Mitchell').should('be.visible');
  cy.compareSnapshot('risk-profile-sidebar-initial');
});
```

```bash
# Generate baseline
npm run cy:update-snapshots:spec "src/components/RiskProfileSidebar/RiskProfileSidebar.spec.tsx"
# Creates: cypress-visual-screenshots/baseline/risk-profile-sidebar-initial.png
```

**Step 6: Iterate and enhance** — add features, update tests, regenerate baselines incrementally.

---

## 18. Training Examples

### Example 1: Fixing a Visual Bug (Overflow Issue)

**Before:**
```typescript
// Test fails: "Sleep & recovery button not visible"
cy.contains('Sleep & recovery').should('be.visible');
```

**Diagnosis:**
```bash
# Check screenshot
open cypress/screenshots/landing-page.cy.ts/failure.png
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
npm run cy:update-snapshots
git commit -m "fix: sidebar overflow clipping bug - Updated visual baseline"
```

### Example 2: Fixing Placeholder Text Assertion

**Before:**
```typescript
// Test fails: can't find placeholder text
cy.contains("Ask about nutrition, exercise, finding a doctor...").should("be.visible");
```

**Fix:**
```typescript
// cy.contains() looks for visible text nodes, not placeholder attributes
cy.get('input[placeholder*="Ask about nutrition"]').should("be.visible");
```

---

## Quick Reference Card

| **Do** | **Don't** |
|--------|-----------|
| Use `cy.compareSnapshot()` | Use `cy.matchImageSnapshot()` (wrong library) |
| Use semantic selectors (`aside`, `main`, class names) | Rely on `data-testid` (not used in this project) |
| Wait for elements to load | Use `cy.wait()` arbitrarily |
| Scope to stable regions | Blindly update snapshots |
| Use meaningful snapshot names | Ignore diff reviews |
| Run tests via Husky pre-push hook | Run visual tests locally only |
| Commit baselines to Git | Store snapshots only locally |
| Mock dynamic content via `cy-mockapi` | Test with live unpredictable data |
| Use `--env updateSnapshots=true` | Use `UPDATE_SNAPSHOTS=true` (wrong env var) |
| Use `.spec.tsx` for component tests | Use `.cy.tsx` (wrong extension) |

---

## Next Steps

1. **Add visual test scenarios** to critical user flows
2. **Configure browser launch flags** in `cypress.config.ts` for CI consistency
3. **Create baseline snapshots** for current UI state
4. **Add diff artifact upload** to CI workflow

---

**Remember:** Visual regression testing is about catching unintended changes, not preventing intentional ones. Review every diff, understand every failure, and update baselines deliberately.
