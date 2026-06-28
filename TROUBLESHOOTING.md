# TROUBLESHOOTING

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

| Variable | Dev Mode | Build (production) | Notes |
|----------|----------|-------------------|-------|
| `import.meta.env.PROD` | `undefined` ⚠️ | `true` ✅ | Not a real runtime property; only replaced at build time |
| `import.meta.env.DEV` | `true` ✅ | `false` ✅ | Guaranteed by Vite in all modes |
| `!import.meta.env.DEV` | `false` ✅ | `true` ✅ | Reliable production check |

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

**Solution:** Use the official `@tailwindcss/vite` plugin which processes Tailwind CSS *before* LightningCSS sees the output.

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
  return (
    <input
      type={type}
      className={cn("...", className)}
      {...props}
    />
  );
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
  }
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
cy.contains("Ask about nutrition, exercise, finding a doctor...").should("be.visible");

// ✅ AFTER
cy.get('input[placeholder*="Ask about nutrition"]').should("be.visible");
```

**Root cause analysis checklist:**
1. Check parent containers for `overflow-hidden`, `overflow-y-auto`, or `overflow-clip`
2. Check if the Cypress viewport size is smaller than the content height
3. Check if the element is a placeholder (use attribute selector, not `cy.contains()`)
4. Check if the element is inside a scrollable container (use `scrollIntoView()`)

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

**See also:** [Visual Regression Playbook](./docs/VISUAL_REGRESSION_PLAYBOOK.md) for complete TDD workflow and component testing strategy.

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
