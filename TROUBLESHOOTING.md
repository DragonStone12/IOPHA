# TROUBLESHOOTING

## Table of Contents

| #   | Section                                                                                | Description                                                        |
| --- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| 1   | [Vite Configuration](#vite-configuration)                                              | `import.meta.env.PROD` undefined pitfall                           |
| 2   | [IOPHA Resources Integration](#iophha-resources-integration)                           | Component copying, `use client`, Tailwind v4, Input ref forwarding |
| 3   | [Cypress E2E: Overflow Clipping](#cypress-e2e-test-element-clipped-by-overflow-parent) | Elements hidden by `overflow` CSS                                  |
| 4   | [Duplicate Text Labels](#duplicate-text-labels-across-sidebar-and-chat-area)           | Sidebar vs chat area click targets                                 |
| 5   | [Visual Testing TDD](#proactive-visual-testing-strategy-tdd-approach)                  | Test-driven visual development workflow                            |
| 6   | [Radix UI Peer Dependencies](#radix-ui-peer-dependencies)                              | Required `@radix-ui/*` packages                                    |
| 7   | [Cypress Component Testing](#cypress-component-testing)                                | Config, patterns, React import error                               |
| 8   | [Logging & Performance](#logging--performance)                                         | Logger, `useLogRenders`, `usePerformanceTracking`                  |
| 9   | [Known Limitations](#known-limitations)                                                | Resource library gaps, calendar styling                            |
| 10  | [Cypress Component Test Flakiness](#cypress-component-test-flakiness)                  | Dynamic dates, fragile calendar DOM, computed CSS in tests         |
| 11  | [Backend Global Exception Handler Re-Raises in Tests](#backend-global-exception-handler-re-raises-in-tests) | `TestClient` raises the original error instead of returning the 500 payload |
| 12  | [Backend PHI Scrubber Leaves JSON Secret Values Exposed](#backend-phi-scrubber-leaves-json-secret-values-exposed) | `"secret": "shh-99"` masks only the key; `TestClient` `AttributeError` in `test_tips_logging.py` |
| 13  | [AWS Lambda Rejects ECR Image (Media Type Not Supported)](#aws-lambda-rejects-ecr-image-media-type-not-supported) | OCI image index + BuildKit attestation manifest vs Lambda's single-manifest requirement |

## Vite Configuration

### Environment Variable Pitfall

**Error:**

```
TypeError: Cannot read properties of undefined (reading 'PROD')
```

Or silently: the app renders an empty page with no React content.

**Cause:** Using `import.meta.env.PROD` is not a stable Vite runtime variable. In dev mode, `import.meta.env.PROD` is `undefined`, causing silent crashes when used in conditionals. Only `DEV`, `MODE`, `BASE_URL`, and `SSR` are guaranteed by Vite.

**Affected files:**

- `IOPHA-frontend/src/utils/logger.ts` (line 2, 27, 31, 35)
- `IOPHA-frontend/src/utils/performance.js` (line 7)

**Solution:** Replace all instances of `import.meta.env.PROD` with `!import.meta.env.DEV`.

| Variable               | Dev Mode       | Build (production) | Notes                                                    |
| ---------------------- | -------------- | ------------------ | -------------------------------------------------------- |
| `import.meta.env.PROD` | `undefined` ⚠️ | `true` ✅          | Not a real runtime property; only replaced at build time |
| `import.meta.env.DEV`  | `true` ✅      | `false` ✅         | Guaranteed by Vite in all modes                          |
| `!import.meta.env.DEV` | `false` ✅     | `true` ✅          | Reliable production check                                |

**Fix in `logger.ts`:**

```typescript
// ❌ BEFORE
private static isProd = import.meta.env.PROD;

// ✅ AFTER
private static isProd = !import.meta.env.DEV;
```

**Fix in `performance.js`:**

```javascript
// ❌ BEFORE
const isProd = import.meta.env.PROD;

// ✅ AFTER
const isProd = !import.meta.env.DEV;
```

## IOPHA Resources Integration

### Component Copying

UI components from IOPHA Resources (`/Users/dragonstone/Development/IOPHA/IOPHA Resources/`) are copied into `IOPHA-frontend/src/components/ui/` rather than imported as a package. This approach was chosen because:

- IOPHA Resources is a separate project with its own `node_modules`, `vite.config.ts`, and build pipeline.
- The story requires using components "exclusively from the IOPHA Resources directory" — copying ensures exact same implementations.
- Direct package imports are not feasible without publishing to a registry or using monorepo tooling.

### `"use client"` Directives

Components copied from IOPHA Resources include `"use client"` directives (Next.js convention). These have been **removed** from all copied components as they are not needed in Vite/React 18. If you encounter build errors related to this, verify the directive has been removed.

### Tailwind CSS v4 Configuration

The project uses Tailwind CSS v4 with the `@tailwindcss/vite` plugin. The theme is defined in `src/index.css` and copied from IOPHA Resources' `theme.css`.

**Required setup:**

- Install `@tailwindcss/vite` plugin
- Add `tailwindcss()` to Vite plugins array in `vite.config.ts`
- Do NOT use `@import "tailwindcss"` in CSS files — the Vite plugin handles this

**Common issues:**

#### CSS Parsing Failure During Build

**Error:**

```
[plugin vite:css-post]
SyntaxError: [lightningcss minify] Unexpected token Function("source")
1  |  @media source(none){
   |        ^
```

**Cause:** Vite defaults to `lightningcss` for CSS minification. LightningCSS does not support Tailwind v4's `@source` or `@theme` at-rule syntax, causing the build to crash.

**Solution:** Use the official `@tailwindcss/vite` plugin which processes Tailwind CSS _before_ LightningCSS sees the output.

1. Install the plugin: `npm install -D @tailwindcss/vite`
2. Update `vite.config.ts`:
   ```typescript
   import tailwindcss from "@tailwindcss/vite";
   export default defineConfig({
     plugins: [react(), tailwindcss()],
   });
   ```
3. Remove `@import "tailwindcss"` from `src/index.css` — the plugin handles it automatically.

#### CSS Variables Not Applying

- Ensure `@theme inline` block is present in `index.css` and processed by the Tailwind Vite plugin.
- Verify `index.css` is imported in `app.tsx` before any component imports.

#### Components Not Styled

- Verify `index.css` is imported in `app.tsx` before any component imports.
- Ensure the Tailwind Vite plugin is active in `vite.config.ts`.

### Input Component Ref Forwarding

**Error:**

```
Warning: Function components cannot be given refs. Attempts to access this ref will fail. Did you mean to use React.forwardRef()?
```

**Cause:** The `Input` component from `src/components/ui/input.tsx` is a regular function component that doesn't support refs. When `ChatArea` tries to pass `ref={inputRef}` for auto-focus functionality, React throws this warning and `inputRef.current` remains `null`.

**Affected files:**

- `IOPHA-frontend/src/components/ui/input.tsx`
- `IOPHA-frontend/src/components/ChatArea/ChatArea.tsx` (line 38, 40)

**Solution:** Update the `Input` component to use `React.forwardRef()`:

```tsx
// ❌ BEFORE
function Input({ className, type, ...props }: InputProps) {
  return <input type={type} className={cn("...", className)} {...props} />;
}

// ✅ AFTER
const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn("...", className)}
        ref={ref}
        {...props}
      />
    );
  },
);
Input.displayName = "Input";
```

**Key changes:**

1. Wrap component with `React.forwardRef()` to accept `ref` as second parameter
2. Pass `ref` to the underlying `<input>` DOM element
3. Add `displayName` for React DevTools debugging

**Verification:**

- Console warning disappears
- `inputRef.current?.focus()` in `ChatArea.tsx` works correctly
- Input auto-focuses on page load as intended

**Note:** This is the standard pattern for all form components (Input, Select, Textarea) when programmatic DOM access is needed. Apply the same pattern to other form components if they need ref support.

### Cypress E2E Test: Element Clipped by Overflow Parent

**Error:**

```
AssertionError: Timed out retrying after 4000ms: expected '<button...>' to be 'visible'

This element is not visible because its content is being clipped by one of its
parent elements, which has a CSS property of overflow: `hidden`, `clip`, `scroll` or `auto`
```

**Cause:** A parent container has `overflow-hidden` or `overflow-y-auto` that clips child elements when the content exceeds the container bounds. In Cypress headless mode, the default viewport (1000x660) is smaller than typical desktop viewports, causing sidebar or page content to overflow and get clipped. `cy.contains().should("be.visible")` fails because the element exists in the DOM but is not visually visible.

**Affected files:**

- `IOPHA-frontend/src/components/LandingPage/LandingPage.tsx` (parent flex container)
- `IOPHA-frontend/src/components/RiskProfileSidebar/RiskProfileSidebar.tsx` (sidebar)
- `IOPHA-frontend/cypress/e2e/landing-page.cy.ts`
- `IOPHA-frontend/cypress/e2e/react-query-integration.cy.ts`

**Solution (choose one):**

**Option A: Remove overflow constraint from parent (preferred for fixed-height layouts)**

If the design expects all content to be visible without scrolling, remove `overflow-hidden` from the parent container:

```tsx
// ❌ BEFORE
<div className="flex flex-1 w-full overflow-hidden">

// ✅ AFTER
<div className="flex flex-1 w-full">
```

Also remove `overflow-y-auto` from the sidebar if content should always be visible:

```tsx
// ❌ BEFORE
<aside className="w-80 shrink-0 bg-card border-r border-border flex flex-col overflow-y-auto">

// ✅ AFTER
<aside className="w-80 shrink-0 bg-card border-r border-border flex flex-col">
```

**Option B: Use `scrollIntoView()` in tests (when overflow is intentional)**

If the container is meant to be scrollable, scroll the element into view before asserting visibility:

```typescript
// ❌ BEFORE
cy.contains("Sleep & recovery").should("be.visible");

// ✅ AFTER
cy.contains("Sleep & recovery").scrollIntoView().should("be.visible");
```

**Option C: Fix placeholder text assertions**

`cy.contains()` looks for visible text nodes, not `placeholder` attributes. Use attribute selectors for input placeholders:

```typescript
// ❌ BEFORE
cy.contains("Ask about nutrition, exercise, finding a doctor...").should(
  "be.visible",
);

// ✅ AFTER
cy.get('input[placeholder*="Ask about nutrition"]').should("be.visible");
```

**Root cause analysis checklist:**

1. Check parent containers for `overflow-hidden`, `overflow-y-auto`, or `overflow-clip`
2. Check if the Cypress viewport size is smaller than the content height
3. Check if the element is a placeholder (use attribute selector, not `cy.contains()`)
4. Check if the element is inside a scrollable container (use `scrollIntoView()`)

### Duplicate Text Labels Across Sidebar and Chat Area

**Error:**

```
AssertionError: Timed out retrying after 4000ms: Expected to find content: 'irregular meal timing' but never did.
```

The `NutritionResponse` component never renders after clicking the "Weight & nutrition tips" chip. The chat area shows the initial greeting and chips but no response content appears.

**Cause:** Both `RiskProfileSidebar` and `ChatArea` render buttons with identical text labels (e.g., "Weight & nutrition tips", "Find a doctor", "Exercise guidance", "Sleep & recovery"). The sidebar buttons are static navigation items with **no `onClick` handler**. When a Cypress step definition uses `cy.contains(chipLabel).click()`, Cypress matches the **first** element in DOM order — the sidebar button. Since it has no handler, `activeTopic` is never set and `NutritionResponse` never mounts.

**Affected files:**

- `IOPHA-frontend/src/components/ChatArea/ChatArea.tsx` (line 25 — interactive chip with `value: "nutrition_tips"`)
- `IOPHA-frontend/src/components/RiskProfileSidebar/RiskProfileSidebar.tsx` (line 180 — static nav item with no handler)
- `IOPHA-frontend/cypress/support/step_definitions/app.steps.ts` (step definition for chip click)

**Solution:** Scope the click selector to the chat area container (`<main>`) so Cypress targets the interactive chip instead of the sidebar button:

```typescript
// ❌ BEFORE — matches sidebar button first (no handler)
When("I click the {string} chip", (chipLabel: string) => {
  cy.contains(chipLabel).click();
});

// ✅ AFTER — scoped to the chat area
When("I click the {string} chip", (chipLabel: string) => {
  cy.get("main").contains(chipLabel).click();
});
```

**Why this works:** The `<main>` element wraps the `ChatArea` component. Scoping `cy.contains()` to `cy.get("main")` restricts the search to the chat area's DOM subtree, bypassing the sidebar's duplicate labels entirely.

**Diagnosis steps:**

1. Open Cypress in headed mode: `npx cypress open --e2e`
2. Watch the test — if the chip appears clicked but no response renders, check which element was actually clicked
3. Inspect the DOM: both sidebar and chat area contain elements with the same text
4. Check the click handler: sidebar buttons have no `onClick`, chat area buttons call `handleTopicClick()`

**Prevention:** When writing E2E step definitions that interact with elements whose labels may appear in multiple regions of the page, always scope the selector to the correct container (`main`, `aside`, a specific `data-testid`, etc.).

### Multiple Matching Step Definitions (Duplicate Steps)

**Error:**

```
Error: Multiple matching step definitions for: I should see introductory text mentioning "ACSM protocol" and "BMI"
 I should see introductory text mentioning {string} and {string}
 I should see introductory text mentioning {string} and {string}
```

The E2E test fails immediately with a `MultipleDefinitionsError` before any assertions run. The error lists the same step pattern twice, indicating two files registered the same step.

**Cause:** The same step definition (e.g., `Then("I should see introductory text mentioning {string} and {string}", ...)`) is defined in more than one `.steps.ts` file. Cucumber loads all step definition files at runtime, and when two files register the same pattern, it cannot determine which implementation to use and throws a `MultipleDefinitionsError`.

This commonly happens when a developer copies an existing feature's step file as a starting point for a new feature, without removing steps that are already defined in `app.steps.ts` or in other feature-specific files.

**Affected files (example):**

- `IOPHA-frontend/cypress/support/step_definitions/exercise-guidance.steps.ts` — defined `I should see introductory text mentioning {string} and {string}`
- `IOPHA-frontend/cypress/support/step_definitions/sleep-recovery.steps.ts` — defined the same step

**Solution:** Move the shared step to `app.steps.ts` and remove it from all feature-specific files. Only steps unique to a single feature should remain in that feature's `.steps.ts` file.

```typescript
// ✅ app.steps.ts — shared steps used by multiple features
Then(
  "I should see introductory text mentioning {string} and {string}",
  (keyword1: string, keyword2: string) => {
    cy.contains(keyword1).scrollIntoView().should("be.visible");
    cy.contains(keyword2).scrollIntoView().should("be.visible");
  },
);

Then("the first card should be titled {string}", (title: string) => {
  cy.get('[aria-posinset="1"]').contains(title).should("be.visible");
});

// ✅ exercise-guidance.steps.ts — only steps unique to exercise guidance
Then(
  "I should see {int} numbered exercise recommendation cards",
  (count: number) => {
    cy.get("[aria-posinset]").should("have.length", count);
  },
);

// ✅ sleep-recovery.steps.ts — only steps unique to sleep recovery
Then(
  "I should see {int} numbered sleep recommendation cards",
  (count: number) => {
    cy.get("[aria-posinset]").should("have.length", count);
  },
);
```

**Diagnosis steps:**

1. Run the duplicate check script:
   ```bash
   npm run cy:check-steps
   ```
2. If the script doesn't catch it (e.g., the duplicate is with a step in `main` that hasn't been merged yet), search manually:
   ```bash
   grep -r "I should see introductory text mentioning" cypress/support/step_definitions/
   ```
3. Identify all files that define the same step pattern
4. Determine which steps are shared (used by multiple features) vs. feature-specific
5. Move shared steps to `app.steps.ts`, remove duplicates from feature files

**Why this passes locally but fails in CI:**

If one feature file was added in a previous PR (already in `main`) and a new feature file copies the same steps, local tests pass because the branch only contains the new file in isolation. CI runs against the **PR merge commit** (branch + main), which loads both files and triggers the duplicate error. The `cy:check-steps` script only checks within the current branch, so it cannot detect conflicts with `main`.

**Prevention:**

- When creating a new feature's step file, start with an empty file — do NOT copy another feature's step file
- Before writing a new step, search for existing definitions: `grep -r "step text" cypress/support/step_definitions/`
- If a step is used by more than one `.feature` file, it belongs in `app.steps.ts`
- Run `npm run cy:check-steps` before pushing (the pre-push hook does this automatically)

### Proactive Visual Testing Strategy (TDD Approach)

To avoid reactive test-fixing cycles, adopt a **test-driven visual development** workflow:

**The Problem:** Writing tests after components are built leads to stale baselines, reactive fixes, and tests that don't reflect design intent.

**The Solution:** Build components with tests from the start, updating visual baselines incrementally.

#### TDD Cycle for Visual Components

```
Write Test → Run (Fails) → Write Minimal Component → Generate Baseline → Iterate
```

**Step-by-step:**

1. **Write the component test first** — before any component code:

   ```typescript
   // src/components/MyComponent/MyComponent.spec.tsx
   import { MyComponent } from './MyComponent';

   describe('MyComponent', () => {
     it('should render correctly', () => {
       cy.mount(<MyComponent />);
       cy.contains('Expected text').should('be.visible');
     });
   });
   ```

2. **Run test (it fails)** — component doesn't exist yet:

   ```bash
   npx cypress run --component --spec "src/components/MyComponent/MyComponent.spec.tsx"
   ```

3. **Create minimal component** — just enough to pass:

   ```tsx
   export function MyComponent() {
     return <div>Expected text</div>;
   }
   ```

4. **Add visual snapshot and generate baseline**:

   ```typescript
   it('should render correctly', () => {
     cy.mount(<MyComponent />);
     cy.contains('Expected text').should('be.visible');
     cy.compareSnapshot('my-component-initial');
   });
   ```

   ```bash
   npm run cy:update-snapshots:spec "src/components/MyComponent/MyComponent.spec.tsx"
   ```

5. **Iterate and enhance** — add features, update tests, regenerate baselines incrementally.

#### When to Update Baselines

**✅ DO Update When:**

- Intentionally changing component design (new features, UI improvements)
- Fixing visual bugs (like overflow issues)
- Adjusting spacing, colors, typography per design specs
- First time creating a component

**❌ DO NOT Update When:**

- Tests fail due to bugs or unintended changes
- Layout breaks accidentally
- Content is clipped or overflow issues occur (fix the code first)
- Tests fail due to dynamic content (dates, times) — mock the data instead

#### Standard Update Workflow

**Scenario 1: Intentional Design Change**

```bash
# 1. Make code changes
# 2. Run tests to see what broke
npm run test:e2e
# 3. Review diff images in cypress-visual-screenshots/diff/
# 4. If changes look correct, update baseline
npm run cy:update-snapshots
# 5. Commit with clear message explaining changes
git add cypress-visual-screenshots/baseline/
git commit -m "chore: update visual baseline for [feature] [snap-update]"
```

**Scenario 2: Fixing Visual Bugs (Like Overflow)**

```bash
# 1. Identify the bug (e.g., "element not visible due to overflow clipping")
# 2. Fix the code (e.g., remove overflow-y-auto)
# 3. Run tests — should pass
npm run test:e2e
# 4. Update baseline to reflect the fix
npm run cy:update-snapshots
# 5. Commit fix + baseline update together
git add src/components/... cypress-visual-screenshots/baseline/
git commit -m "fix: [description] - Updated visual baseline"
```

**See also:** [Visual Regression Playbook](./docs/testing/VISUAL_REGRESSION_PLAYBOOK.md) for complete TDD workflow and component testing strategy.

### Radix UI Peer Dependencies

Components from IOPHA Resources depend on `@radix-ui/*` packages. All required peer dependencies must be installed in `IOPHA-frontend`:

```bash
npm install @radix-ui/react-avatar @radix-ui/react-progress @radix-ui/react-separator @radix-ui/react-tooltip @radix-ui/react-slot
```

## Cypress Component Testing

### Component Test Configuration

Component tests are configured in `cypress.config.ts` under the `component` key. The test spec pattern is `src/components/**/*.spec.tsx`.

**Common issues:**

- **Tests not running**: Verify `cypress.config.ts` has the `component` configuration block.
- **CSS not loading**: Ensure `cypress/support/component.ts` imports `../../src/index.css`.
- **Vite not found**: The component test dev server uses Vite as the bundler. Ensure Vite is installed.

### Component Test Patterns

Each component test file follows this pattern:

1. Mount the component with `cy.mount(<Component props />)`
2. Assert rendered content with `cy.contains()` or `cy.get()`
3. Test interactions with `cy.contains().click()`

### Cypress React Import Error (Cypress 13+)

**Error:**

```
"./react18" is not exported under the conditions ["module", "browser", "development", "import"]
from package /path/to/node_modules/cypress
```

Or at runtime:

```
Failed to fetch dynamically imported module: http://localhost:3000/__cypress/src/cypress/support/component.ts
```

**Cause:** Cypress 13+ consolidated the React mounting adapter into a single `cypress/react` package. The old `cypress/react18` and `cypress/react17` subpath exports no longer exist. If `cypress/support/component.ts` uses `import { mount } from "cypress/react18"`, Vite cannot resolve the module and all component tests fail before they start.

**Affected files:**

- `IOPHA-frontend/cypress/support/component.ts`

**Solution:** Change the import from `cypress/react18` to `cypress/react`:

```typescript
// ❌ BEFORE (Cypress < 13)
import { mount } from "cypress/react18";

// ✅ AFTER (Cypress 13+)
import { mount } from "cypress/react";
```

The `mount` function from `cypress/react` automatically detects and works with React 18. No other changes are needed — all existing component tests will work with this single-line fix.

**Verification:**

```bash
npx cypress run --component --spec "src/components/NutritionResponse/NutritionResponse.spec.tsx"
# Should show: 12 passing
```

**Note:** This is a project-wide fix. All component tests (ChatArea, LandingPage, RiskProfileSidebar, NutritionResponse, etc.) share the same `cypress/support/component.ts` support file, so fixing the import resolves the issue for every component test at once.

## Cypress Component Test Flakiness

Component tests (e.g., `TimeSelector.spec.tsx`) intermittently fail with no code changes — a button with a specific label (e.g. `"09:00 AM"`) is sometimes absent, so `cy.contains("button", "09:00 AM")` times out. The root cause is **non-deterministic mock data in the component under test**, not dates, calendar queries, or computed CSS.

**Root cause & fix:**

1. **Non-deterministic mock data (the actual cause)** — `TimeSelector.generateMockSlots` used `Math.random() > 0.3` to set each slot's `available` flag, and the component renders only `slots.filter((s) => s.available)`. ~30% of runs the specific slot the test queries (`"09:00 AM"`) is randomly filtered out, so its button never renders. **Fix:** make slot availability deterministic by deriving it from the slot index (e.g. `available: (i + 1) % 3 !== 0`) so rendering is reproducible. Tests should also avoid asserting on a specific randomly-available label — interact with a slot that is actually rendered (the `button[aria-label*='Select']` pattern) instead.

The following hardening practices prevent a related but distinct class of flakes. They are still recommended and are already applied to `TimeSelector.spec.tsx`, but they were **not** the cause of this flake:

2. **Freeze the clock** — use `cy.clock()` with a static `BASELINE_DATE` so date-dependent rendering is stable across runs/timezones.
3. **Query only `:visible` elements** — add `.filter(":visible")` before `.first()` on calendar/grid chains to avoid clicking non-interactive cells.
4. **Assert DOM state, not computed CSS** — prefer `.should("have.class", ...)` / `.should("exist")` over `have.css` pixel values, which vary by headless mode and sub-pixel rounding.
5. **Use attribute-scoped selectors** — `cy.contains("button", "09:00 AM")` is less specific than `button[aria-label*="Select"]` because it matches the first button in DOM order, which may belong to a different component. Always scope selectors to the target element using stable attributes like `aria-label`.

**Global `Math.random` stub removed:** The global `cy.stub(win.Math, "random").returns(0.4)` in `cypress/support/component.ts` was removed because it masked the non-deterministic mock data bug and affected every component test. If a specific test needs deterministic random values, stub `Math.random` locally inside that test's `it` block instead.

**Snapshot threshold significance:** `SNAPSHOT_TEST_THRESHOLD` was lowered from `0.5` (50% pixel tolerance — too loose to catch real regressions) to `0.02` in `cypress.config.ts`. At `0.02`, snapshot baselines must exactly reflect the current deterministic rendering. Baselines live in `cypress-visual-screenshots/baseline/` and are **gitignored (environment-specific)** — they are regenerated locally / in CI, not committed. After any change to a component's rendered output, regenerate the baselines (delete the stale PNGs and re-run the component specs) or the snapshot tests will fail at the strict threshold.

**Avoiding flaky snapshot failures:** (1) Every `cy.compareSnapshot` call needs a **unique `name`** — two tests sharing a name overwrite the same baseline PNG and then diff against each other (e.g. one capturing a transient validation-error border the other didn't). (2) **Snapshot only a settled state** — assert transient UI (validation errors, spinners) has resolved before `cy.compareSnapshot`. (3) Keep component renders **deterministic** (no `Math.random()` / `new Date()`). (4) Because baselines are gitignored and font rendering differs per machine, **regenerate baselines per environment** after render changes; a too-low threshold only trades coverage for sensitivity to sub-pixel / font differences — fix the determinism, don't loosen the threshold. See [Cypress Test Stability Best Practices](../docs/CYPRESS_TESTING.md#best-practices-test-stability).

**Affected files:**

- `IOPHA-frontend/src/components/booking/TimeSelector.tsx` (`generateMockSlots`)
- `IOPHA-frontend/src/components/booking/TimeSelector.spec.tsx`
- `IOPHA-frontend/cypress.config.ts` (`SNAPSHOT_TEST_THRESHOLD`)

## Logging & Performance

### Logger

The custom `Logger` class (`src/utils/logger.ts`) suppresses `debug`, `info`, and `warn` in production. Only `error` is always emitted.

### useLogRenders Hook

Use `useLogRenders("ComponentName", trackedProps)` at the top of each component to track render frequency. Logs render count and prop snapshot via `Logger.debug`.

### usePerformanceTracking Hook

Use `usePerformanceTracking()` at the top of each component to capture render duration. Warns if render exceeds 16ms (60fps threshold) via `Logger.warn`.

## Known Limitations

### No Resource Library Gaps Encountered

During implementation of the Landing Page, all required components (Avatar, Badge, Button, Input, Progress, Separator, Skeleton, Tooltip) were available in IOPHA Resources and copied successfully. No workarounds were needed.

### Calendar Styling

Calendar picker styles from `globals.css` are included in `index.css` for future use (booking flow). These styles target `.rdp-*` classes from the `react-day-picker` library, which is not yet installed.

## Backend Global Exception Handler Re-Raises in Tests

### Symptom

A route that raises a raw, unhandled exception (e.g. `RuntimeError`) is meant
to be caught by the global `Exception` handler in `IOPHA-backend/app/utils/handlers.py`
(`_global_unexpected_handler`), which returns a structured `500` JSON payload
with a `help_url` runbook link. Under `FastAPI.testclient.TestClient`, the test
fails with the **original** exception raised instead of a `500` response:

```
RuntimeError: simulated unhandled fault
```

### Root Cause

`app.add_exception_handler(Exception, ...)` is wired into Starlette's
`ServerErrorMiddleware` (the outermost middleware), not the inner
`ExceptionMiddleware`. `ServerErrorMiddleware.__call__` deliberately **re-raises
the exception after** it has built and sent the response:

```python
# We always continue to raise the exception.
# This allows servers to log the error, or allows test clients
# to optionally raise the error within the test case.
raise exc
```

In production (uvicorn), that re-raise is caught by the server and logged; the
client still receives the `500` JSON from the handler. But `TestClient` defaults
to `raise_server_exceptions=True`, so it surfaces the re-raised error into the
test instead of returning the response object.

This only affects the global `Exception` handler. Domain exceptions
(`RaceConditionDoubleBookingError`, etc.) are caught one layer deeper by
`ExceptionMiddleware`, which returns the response **without** re-raising, so
their tests behave normally.

### Solution

When testing the global handler, construct the `TestClient` with
`raise_server_exceptions=False` so the test can assert on the returned `500`
payload rather than the re-raised error:

```python
from fastapi.testclient import TestClient

client = TestClient(app, raise_server_exceptions=False)
response = client.get("/errors/unexpected")
assert response.status_code == 500
assert response.json()["help_url"].endswith("#internal-server-error")
```

Do **not** disable `raise_server_exceptions` to hide unrelated server faults —
only use it for the specific tests that exercise the global `500` handler.

## Backend PHI Scrubber Leaves JSON Secret Values Exposed

### Symptom

`PHIScrubber.scrub_message` masked the credential **key** but left the **value**
exposed for JSON-style pairs:

```python
scrubber.scrub_message('payload {"secret": "shh-99"} done')
# Expected: 'payload {[MASKED]} done'
# Actual:   'payload {"[MASKED]": "shh-99"} done'
```

The `key=value` form (`password=hunter2`) was already correct, only the
`"key": "value"` form leaked.

Separately, running the suite surfaced a failure in
`tests/unit/test_tips_logging.py`:

```
AttributeError: module 'fastapi' has no attribute 'TestClient'
```

which (after the first edit) became:

```
NameError: name 'TestClient' is not defined
```

### Why the earlier attempts didn't work

The value class in the JSON pattern (`[^\s,"]+`) was not the root cause. Two
red herrings were chased first:

1. **"The value class stops at the closing quote."** Making it inclusive of
   quotes would capture the value, but the real problem was upstream: the whole
   value syntax never even applied to the `secret` key (see below), so the value
   was never reached by the match.
2. **Pattern-ordering / single-combined-alternation theories.** The scrubber
   deliberately concatenates every pattern into one alternation run in a single
   `sub` pass to avoid re-mangling output, so "reorder the patterns" was not the
   fix.

The actual bug is the **regex operator-precedence trap**: the JSON pattern
injected the `_CREDENTIAL_KEYS` string (which contains `|` alternation) into the
pattern **without** wrapping it in a non-capturing group:

```python
# BROKEN — keys are not grouped, so \s*:\s*... binds only to the LAST key
re.compile(rf'["\']?{_CREDENTIAL_KEYS}["\']?\s*:\s*["\']?[^\s,"]+["\']?')
```

Because `|` is a top-level alternation operator, the engine parses this as
`["\']?password` OR `passwd` OR ... OR `secret` OR ... OR
`session[_-]?id["\']?\s*:\s*["\']?[^\s,"]+["\']?`. The trailing value syntax
(`\s*:\s*["\']?[^\s,"]+["\']?`) attaches **only to the last key**
(`session[_-]?id`). For `"secret": "shh-99"` the engine matches the bare
`secret` branch and stops — the `: "shh-99"` portion is never consumed. (The
`key=value` pattern on the line above already wrapped its keys in `(?:...)`,
which is why it worked.)

The `__import__` theory for the test failure was also a red herring until the
import itself was inspected: the test called
`__import__("fastapi.testclient").TestClient(app)`. Python's `__import__` returns
the **top-level** package for a dotted name, so it returned the `fastapi` module
(which has no `TestClient` attribute) rather than the `fastapi.testclient`
submodule → `AttributeError`.

### What finally worked

**1. Wrap the keys in a non-capturing group** so the value syntax applies to
*every* key (`app/core/phi_scrubber.py`):

```python
# FIXED — grouped, so \s*:\s*... binds to all keys
re.compile(rf'["\']?(?:{_CREDENTIAL_KEYS})["\']?\s*:\s*["\']?[^\s,"]+["\']?'),
```

The value class was left as-is (it already consumes the value's surrounding
quotes via the optional `["\']?` on each side). Result:
`'payload {"secret": "shh-99"} done'` → `'payload {[MASKED]} done'`.

**2. Fix the test** (`tests/unit/test_tips_logging.py`):

- A previous `ruff` run (F401 "imported but unused") had **removed** the
  `from fastapi.testclient import TestClient` import, because the only reference
  to `TestClient` was the broken `__import__(...)` call. Restore it:
  ```python
  from fastapi.testclient import TestClient
  ```
- Replace the `__import__` call with the already-imported name:
  ```python
  # ❌ BEFORE
  with __import__("fastapi.testclient").TestClient(app) as client:
  # ✅ AFTER
  with TestClient(app) as client:
  ```

### Verification

```bash
cd IOPHA-backend
PYTHONPATH=. venv/bin/python -c "
from app.core.phi_scrubber import PHIScrubber
print(PHIScrubber().scrub_message('payload {\"secret\": \"shh-99\"} done'))
"   # -> payload {[MASKED]} done

PYTHONPATH=. venv/bin/python -m pytest tests/unit/test_tips_logging.py -q   # 9 passed
PYTHONPATH=. venv/bin/python -m pytest -q                                  # 204 passed
venv/bin/ruff check app tests                                               # All checks passed!
```

### Rule of thumb

Whenever you interpolate a variable that contains regex alternation (`|`) into a
larger pattern, **always** wrap it in `(?:...)` so the surrounding syntax binds
to the whole alternation, not just the last branch.

## AWS Lambda Rejects ECR Image (Media Type Not Supported)

**Error (AWS Lambda console, "Create function" → "Container image"; account ID redacted):**

```
The image manifest, config or layer media type for the source image
<aws-account-id>.dkr.ecr.us-east-2.amazonaws.com/iopha-backend@sha256:<digest> is not supported.
```

**How it occurred:** The image was built and pushed from an Apple Silicon Mac
via `push-to-ecr.sh` using Docker Desktop (BuildKit engine + containerd image
store). Since BuildKit 0.11 / Docker Desktop 4.26, `docker build` attaches a
**provenance attestation manifest** by default, and `docker push` uploads an
**OCI image index** (`application/vnd.oci.image.index.v1+json`) containing two
entries: the real `linux/arm64` image manifest and an attestation manifest
whose platform is `unknown/unknown`. The ECR tag `latest` therefore resolved
to the *index*, not to the image itself, and Lambda refused it when creating
the function.

**What it means:** AWS Lambda imports a container image from ECR only when the
tag resolves directly to a **single image manifest** — Docker Image Manifest V2
Schema 2 (`application/vnd.docker.distribution.manifest.v2+json`) or OCI Image
Manifest v1 (`application/vnd.oci.image.manifest.v1+json`). Lambda does **not**
support OCI image indexes / Docker manifest lists, nor BuildKit attestation
manifests. The error fires before the function is created; nothing is wrong
with the image contents themselves.

**Diagnosis:**

```bash
docker manifest inspect <aws-account-id>.dkr.ecr.us-east-2.amazonaws.com/iopha-backend:latest
```

If the output shows `"mediaType": "application/vnd.oci.image.index.v1+json"`
with a nested entry whose platform is `"architecture": "unknown", "os":
"unknown"`, the tag points to an index + attestation manifest and Lambda will
reject it.

**Solution:** Rebuild with provenance attestations disabled so the push
uploads a plain single-platform manifest. Already applied in `push-to-ecr.sh`:

```bash
# ❌ BEFORE — pushes an OCI image index + attestation manifest
docker build -t ${ECR_REPOSITORY}:${IMAGE_TAG} -f IOPHA-backend/Dockerfile IOPHA-backend

# ✅ AFTER — pushes a single image manifest Lambda can import
docker build --platform linux/arm64 --provenance=false -t ${ECR_REPOSITORY}:${IMAGE_TAG} -f IOPHA-backend/Dockerfile IOPHA-backend
```

Then re-run `bash push-to-ecr.sh` and retry the Lambda function creation.

**Verification:**

```bash
docker manifest inspect <aws-account-id>.dkr.ecr.us-east-2.amazonaws.com/iopha-backend:latest
# ✅ "mediaType": "application/vnd.oci.image.manifest.v1+json" — plain manifest, no index
```

**Architecture pitfall (separate but related):** an image built on Apple
Silicon defaults to `linux/arm64`, while the Lambda console defaults to the
`x86_64` architecture. Select **arm64** when creating the function, or build
with `--platform linux/amd64` (QEMU-emulated, slower). A mismatch fails
function creation with an architecture error *after* the media-type check
passes.

**Affected files:**

- `push-to-ecr.sh` (build command)

## Python Testing Anti-Patterns

### Things to Avoid When Writing Python Tests

#### 1. Do NOT use `app.dependency_overrides.clear()` in teardown

**Error:**

```python
@pytest.fixture(autouse=True)
def bind_mock() -> Generator[None, None, None]:
    app.dependency_overrides[get_tips_repository] = lambda: MockTipsRepository()
    try:
        yield
    finally:
        app.dependency_overrides.clear()  # WRONG — destroys all overrides
```

**Why this is wrong:**

`app.dependency_overrides.clear()` removes **every** dependency override in the FastAPI app, not just the one your test set. If any other test, fixture, or `conftest.py` in the same process has overridden a different dependency (e.g., `get_provider_repository`, `get_calendar_repository`), those overrides are unexpectedly wiped out. This breaks test isolation and causes cascading failures in unrelated test modules.

**Symptom:** A test in `test_providers.py` passes in isolation but fails when run after `test_tips_integration.py`, because the tips fixture cleared the provider repository override that the providers test expected to find.

**Solution:** Pop only the specific key you set:

```python
@pytest.fixture(autouse=True)
def bind_mock() -> Generator[None, None, None]:
    app.dependency_overrides[get_tips_repository] = lambda: MockTipsRepository()
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_tips_repository, None)
```

**Why this works:**

- `pop(key, None)` removes only the override you added, leaving all others intact.
- The `None` default prevents `KeyError` if the key was never set (e.g., if the test skipped the override).
- Other test modules' overrides remain untouched, preserving process-wide test isolation.

**Affected files (fixed):**

- `IOPHA-backend/tests/integration/test_tips_integration.py` — `bind_tips_mock` fixture and `TestTipsDependencyIsolation`
- `IOPHA-backend/tests/unit/test_providers.py` — `isolate_database_layer` fixture

**Correct pattern already in use elsewhere:**

- `tests/integration/test_tips_errors.py` — uses `app.dependency_overrides.pop(get_tips_repository, None)`
- `tests/integration/test_timeslot_full_flow.py` — uses `_clear_mock()` which calls `app.dependency_overrides.pop(get_calendar_repository, None)`
- `tests/integration/test_timeslot_errors.py` — uses `app.dependency_overrides.pop(get_calendar_repository, None)`
- `tests/integration/test_timeslots_success.py` — uses `app.dependency_overrides.pop(get_calendar_repository, None)`

#### 2. Do NOT share mutable state between tests

Never use module-level mutable objects (lists, dicts, sets) as test fixtures without resetting them. Each test must get a fresh copy:

```python
# WRONG — shared across tests
favorites = []

def test_add():
    favorites.append("apple")

def test_count():
    assert len(favorites) == 1  # Fails if test_add ran first

# RIGHT — fixture provides fresh copy
@pytest.fixture
def favorites():
    return []

def test_add(favorites):
    favorites.append("apple")

def test_count(favorites):
    assert len(favorites) == 1  # Always passes
```

#### 3. Do NOT use `try/finally` without `yield` in fixtures

A fixture that sets up state must `yield` to the test, then clean up in `finally`. Returning without yielding means the teardown never runs:

```python
# WRONG — teardown never runs
@pytest.fixture
def db():
    db = create_db()
    db.clear()  # Runs BEFORE the test, not after

# RIGHT — yield separates setup from teardown
@pytest.fixture
def db():
    db = create_db()
    try:
        yield db
    finally:
        db.clear()  # Runs AFTER the test
```

#### 4. Do NOT catch `Exception` without re-raising in tests

Swallowing all exceptions hides test failures and produces false positives:

```python
# WRONG — test passes even when code raises
try:
    do_something()
except Exception:
    pass
assert True

# RIGHT — let pytest see the failure
do_something()
```

#### 5. Do NOT use `time.sleep()` for synchronization

`time.sleep()` makes tests slow and flaky. Use proper synchronization primitives or pytest fixtures:

```python
# WRONG — arbitrary wait
time.sleep(2)
assert db.count() == 1

# RIGHT — fixture waits for condition
@pytest.fixture
def ready_db():
    wait_until(lambda: db.count() == 1)
    return db
```

## Related Documentation

- [Security Overview](../docs/security/SECURITY.md)
- [Sensitive Data Handling](../docs/security/SENSITIVE_DATA_HANDLING.md)
- [Input Validation](../docs/security/INPUT_VALIDATION.md)
- [Technical Design](../docs/infra/TECHNICAL_DESIGN.md)
- [Runbooks](../docs/RUNBOOKS.md)

