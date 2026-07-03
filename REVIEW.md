# Code Review Guidelines

Use this document to verify that submitted code follows IOPHA conventions. A reviewer can confirm compliance by inspecting the code directly.

## Table of Contents

1. [File Structure & Naming](#1-file-structure--naming)
2. [Component Tests](#2-component-tests)
3. [Cypress E2E Tests](#3-cypress-e2e-tests)
4. [Visual Regression Tests](#4-visual-regression-tests)
5. [ESLint & Security Patterns](#5-eslint--security-patterns)
6. [Accessibility & Selectors](#6-accessibility--selectors)
7. [Quick Reference](#7-quick-reference)

---

## 1. File Structure & Naming

- Each React component lives in its own directory under `src/components/`.
- Component tests use `.spec.tsx` and live in the same directory as the component they test.
- UI primitives from IOPHA Resources are placed in `src/components/ui/`.

**Feature docs** in `docs/features/` must follow the `APPOINTMENT_FLOW.md` naming convention (uppercase).

**All Markdown files** must use uppercase names with the `.md` extension (e.g., `SECURITY.md`, `ARCHITECTURE.md`, `APPOINTMENT_FLOW.md`). Any Markdown file with lowercase letters in the filename is a violation.

---

## 2. Component Tests

### Test Presence

Every new component must have a corresponding `.spec.tsx` file. If a component exists under `src/components/X/X.tsx`, then `src/components/X/X.spec.tsx` must also exist.

### Mounting Pattern

Component tests must use `cy.mount()` from `cypress/react`. Do NOT use `cy.visit()` or import from `cypress/react18`.

```typescript
import { mount } from "cypress/react";

cy.mount(<MyComponent prop="value" />);
```

### Assertion Patterns

- Use `cy.contains("text")` for visible text assertions.
- Use `cy.get("input[placeholder*=\"...\"]")` for placeholder attributes (`cy.contains()` does not match placeholders).
- Use `cy.stub().as("callbackName")` for callback verification. Do not verify callbacks by DOM inspection alone.

```typescript
const callback = cy.stub().as("onSelect");
cy.mount(<Component onSelect={callback} />);
cy.contains("Button").click();
cy.get("@onSelect").should("have.been.calledWith", "expected");
```

### Test Independence

Each test must reset shared state in `beforeEach`. Do not share mutable state across `it()` blocks.

---

## 3. Cypress E2E Tests

### Step Definition Uniqueness

Search `cypress/support/step_definitions/` for duplicate step patterns. Each step text must be defined in exactly one file.

- Shared steps (used by multiple features) belong in `app.steps.ts`.
- Feature-specific steps belong in that feature's `.steps.ts` file.
- If two `.steps.ts` files define the same `Given(...)`, `When(...)`, or `Then(...)` pattern with the same text, that is a violation.

### Scoped Selectors

E2E step definitions that click interactive elements must scope selectors to the chat area (`<main>`), not the sidebar.

```typescript
// CORRECT
cy.get("main").contains("Weight & nutrition tips").click();

// INCORRECT — matches sidebar text first
cy.contains("Weight & nutrition tips").click();
```

### Naming Convention

Each `.feature` file in `cypress/e2e/Tests/` must have a corresponding `.steps.ts` file with the same base name:
- `nutrition-tips.feature` → `nutrition-tips.steps.ts`
- `booking-flow.feature` → `booking-flow.steps.ts`

---

## 4. Visual Regression Tests

### Snapshot Presence

Every component test `it()` block that mounts a component must end with exactly one `cy.compareSnapshot()` call. If a component is mounted but no snapshot is taken, that is a violation.

### Snapshot Placement

`cy.compareSnapshot()` must come after all functional assertions (`cy.contains()`, `cy.get()`), not before.

```typescript
it("renders the component", () => {
  cy.mount(<Component />);
  cy.contains("Expected text").should("be.visible");
  cy.compareSnapshot("component-default"); // Must be last
});
```

### Snapshot Naming

Use `<component-name>-<state>` format:
- `landing-page-default`
- `sidebar-high-risk`
- `nutrition-response-default`

Vague names like `test1`, `screenshot`, or `default` are violations.

### Viewport

If the test sets a viewport, it must use 1440x900 as the standard. Tests should not rely on smaller viewports that cause clipping.

---

## 5. ESLint & Security Patterns

### Inline Disable Comments

When an ESLint rule is disabled inline, the scope must be limited to the specific line. File-level or block-level disables for security rules are violations.

```typescript
// CORRECT — single line, specific rule
// eslint-disable-next-line no-secrets/no-secrets
const imageUrl = "https://images.unsplash.com/photo-...";

// INCORRECT — file-level disable
/* eslint-disable no-secrets/no-secrets */
```

### Prohibited Patterns in Source Code

Scan source files for these anti-patterns. Any match is a violation unless accompanied by a narrow inline disable explaining why:

| Pattern | Rule | Severity |
|---|---|---|
| `eval(expression)` | `security/detect-eval-with-expression` | error |
| `child_process.exec`, `spawn`, `execSync` | `security/detect-child-process` | error |
| `fs.readFile(variablePath)` | `security/detect-non-literal-fs-filename` | warn |
| `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write` | XSS risk | error |
| `Math.random()`, `crypto.pseudoRandomBytes` | `security/detect-pseudoRandomBytes` | warn |
| High-entropy strings matching secret patterns | `no-secrets/no-secrets` | error |

### Promise Handling

Every promise chain must end with `.catch()` or return the promise. Unhandled `.then()` chains are violations.

### Regex Safety

Regex patterns with nested quantifiers (e.g., `(a+)+`, `(x*)+`) are ReDoS vulnerabilities and must not appear in source code.

---

## 6. Accessibility & Selectors

### ARIA Attributes

Numbered tip cards and recommendation cards should include `aria-posinset` for accessibility and test stability.

```typescript
<li aria-posinset="1" aria-setsize="3">
  <h3>Tip title</h3>
</li>
```

### Selector Priority

- Use semantic HTML elements (`aside`, `main`, `nav`, `section`) and stable class names.
- Do not use `data-testid` attributes.
- Do not rely on fragile selectors like `.btn-primary` or `button:first`.

### Stub Usage for Callbacks

Callback events must be verified with `cy.stub().as(...)`. Verifying callbacks by checking DOM changes alone is a violation.

---

## 7. Quick Reference

### File Checks

| Check | Violation If... |
|---|---|
| Component test exists | No `.spec.tsx` file alongside component |
| Correct test extension | File uses `.cy.tsx` instead of `.spec.tsx` |
| Correct mount import | Uses `cypress/react18` instead of `cypress/react` |
| Unique step definitions | Same step text appears in multiple `.steps.ts` files |
| Feature-to-steps mapping | `.feature` file has no matching `.steps.ts` file |

### Code Checks

| Check | Violation If... |
|---|---|
| Snapshot present | `cy.mount()` used but no `cy.compareSnapshot()` in the same `it()` |
| Snapshot after assertions | `cy.compareSnapshot()` appears before `cy.contains()` / `cy.get()` |
| Snapshot naming | Name is vague (`test1`, `default`, `screenshot`) |
| Scoped E2E selectors | `cy.contains(label).click()` without `cy.get("main")` scope |
| Inline disable scope | File-level or block-level `eslint-disable` for security rules |
| Prohibited patterns | `eval()`, `innerHTML`, `child_process` without narrow inline disable |
| Promise handling | `.then()` chain without `.catch()` or return |
| Independent tests | Tests share mutable state without `beforeEach` reset |
| Callback verification | Callback checked by DOM only, not `cy.stub()` |
