# Cypress Testing Guide
**For IOPHA Frontend (Cypress 15 + React 18 + Vite + Tailwind CSS v4)**

## Table of Contents

| # | Section | Description |
|---|---------|-------------|
| 1 | [Overview](#overview) | Tech stack and scope |
| 2 | [E2E vs Component Tests](#testing-strategy-e2e-vs-component-tests) | When to use each testing approach |
| 3 | [Component Testing Guide](#cypress-component-testing-guide) | Setup, mounting, props, variants, best practices |
| 4 | [TDD Workflow](#mandatory-tdd-workflow-for-component-tests) | Mandatory test-driven development cycle |
| 5 | [Component vs Integration](#component-level-vs-integration-testing) | Scope and use-case guidance |
| 6 | [Troubleshooting](#troubleshooting) | Common Cypress errors and fixes |
| 7 | [Quick Reference](#quick-reference-card) | Do/Don't cheat sheet |

## Overview

This guide covers all Cypress testing for the IOPHA frontend: E2E tests with Cucumber BDD, component tests, and the mandatory TDD workflow. Visual regression testing is documented separately in `VISUAL_REGRESSION_PLAYBOOK.md`.

**Tech stack:**
- Cypress 15 (E2E + Component Testing via `cy.mount`)
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
    ├── app.feature              # Gherkin feature files (E2E tests ONLY)
    └── nutrition-tips.feature

cypress/support/
└── step_definitions/
    ├── app.steps.ts             # Step definitions for app.feature
    └── nutrition-tips.steps.ts  # Step definitions for nutrition-tips.feature
```

All E2E tests use Gherkin syntax in `.feature` files. Step definitions are in `cypress/support/step_definitions/`.

**Naming convention:** Each `.feature` file MUST have a corresponding `.steps.ts` file with a matching base name. For example, `nutrition-tips.feature` maps to `nutrition-tips.steps.ts`. Step definitions for one feature MUST NOT be placed in another feature's step definition file.

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

### Step Definition Organization Rules

**Each step definition must be unique across all step files.** Cucumber loads all step definitions when running E2E tests, and duplicate definitions cause immediate failures:

```
Error: Multiple matching step definitions for: I should see introductory text mentioning "ACSM protocol" and "BMI"
 I should see introductory text mentioning {string} and {string}
 I should see introductory text mentioning {string} and {string}
```

**Rules:**

1. **Shared steps go in `app.steps.ts`** — Steps used by multiple features (e.g., `Given("I am on the IOPHA homepage")`, `When("I click the {string} chip")`) must be defined only once in `app.steps.ts`.

2. **Feature-specific steps go in dedicated files** — Steps unique to a feature belong in that feature's `.steps.ts` file (e.g., `nutrition-tips.steps.ts` for nutrition-specific assertions).

3. **Never duplicate steps across files** — If a step is needed by multiple features, it belongs in `app.steps.ts`, not duplicated in each feature's file.

4. **Run `npm run cy:check-steps` before pushing** — The pre-push hook runs this automatically, but you can run it manually to check for duplicates:
   ```bash
   npm run cy:check-steps
   ```

**Decision framework — where does this step belong?**

When writing a new step definition, ask: **"Is this step text used by more than one `.feature` file?"**

- **Yes** → Define it in `app.steps.ts`. Do NOT copy it into each feature's step file.
- **No** → Define it in that feature's dedicated `.steps.ts` file.

**Common mistake — copying steps between feature files:**

When creating a new feature file (e.g., `exercise-guidance.feature`), it's tempting to copy an existing feature's step file (e.g., `sleep-recovery.steps.ts`) as a starting point and then modify it. This copies all step definitions, including ones that are already defined in `app.steps.ts` or in other feature files. Even if the step text is identical, Cucumber treats each `Then(...)` / `Given(...)` / `When(...)` call as a separate registration, and two registrations with the same pattern cause a `MultipleDefinitionsError`.

**Real-world example:**

Both `exercise-guidance.steps.ts` and `sleep-recovery.steps.ts` defined identical steps:

```typescript
// ❌ DUPLICATE — defined in both exercise-guidance.steps.ts AND sleep-recovery.steps.ts
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
```

This passed locally when only one feature file existed, but failed in CI when both features ran together because Cucumber loaded all step files and found two registrations for the same pattern.

**Correct approach:**

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

// ✅ exercise-guidance.steps.ts — only feature-specific steps
Then(
  "I should see {int} numbered exercise recommendation cards",
  (count: number) => {
    cy.get("[aria-posinset]").should("have.length", count);
  },
);

// ✅ sleep-recovery.steps.ts — only feature-specific steps
Then(
  "I should see {int} numbered sleep recommendation cards",
  (count: number) => {
    cy.get("[aria-posinset]").should("have.length", count);
  },
);
```

**Why CI caught this but local tests didn't:**

The CI runs tests against the **PR merge commit** (your branch + main). If your branch defines a step that also exists in main, the merge creates duplicates. Local tests only run against your branch in isolation, so they pass. The `cy:check-steps` script catches duplicates within your branch, but cannot predict merge conflicts with main.

**To avoid merge conflicts:**
- Before creating a new step, check if it already exists in `app.steps.ts` or other step files
- When in doubt, use `grep -r "step text" cypress/support/step_definitions/` to search for existing definitions
- When starting a new feature's step file, do NOT copy another feature's step file — start with an empty file and only add steps unique to that feature

### Scoped Selectors for Interactive Elements

When clicking interactive elements (chips, buttons, links) in E2E step definitions, always scope the selector to the correct container. The IOPHA landing page renders duplicate text labels in both the sidebar (`RiskProfileSidebar`) and the chat area (`ChatArea`). Using a bare `cy.contains(label).click()` will match the **first** element in DOM order — which is the sidebar's static navigation item with no click handler — causing the intended action to silently fail.

**Correct pattern** — scope to the chat area (`<main>`):
```typescript
When("I click the {string} chip", (chipLabel: string) => {
  cy.get("main").contains(chipLabel).click();
});
```

This ensures Cypress clicks the interactive chip inside the chat area rather than the non-interactive sidebar navigation item. For more information on diagnosing and resolving this issue, see the [Troubleshooting guide](../TROUBLESHOOTING.md#duplicate-text-labels-across-sidebar-and-chat-area).

**When to use E2E tests:**
- Full page layouts and user flows
- Multi-component interactions
- End-to-end user journeys

### Component Tests (`.spec.tsx`)

Component tests use **Cypress Component Testing** with `cy.mount()` to test components in isolation. Test files use `.spec.tsx` extension and live alongside components in `src/components/`.

**File structure:**
```
src/components/
├── LandingPage/
│   ├── LandingPage.tsx
│   └── LandingPage.spec.tsx    # Component test
── RiskProfileSidebar/
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
import { mount } from "cypress/react";
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

> **Important:** Cypress 13+ consolidated React mounting into `cypress/react`. Do NOT use `cypress/react18` — it does not exist in Cypress 15 and will cause module resolution errors.

**Component mount HTML** (`cypress/support/component-index.html`):
```html
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width,initial-scale=1.0" />
    <title>Components App</title>
  </head>
  <body>
    <div data-cy-root></div>
  </body>
</html>
```

### Running Component Tests

```bash
# Run all component tests
npx cypress run --component

# Run a specific component test
npx cypress run --component --spec "src/components/NutritionResponse/NutritionResponse.spec.tsx"

# Open Cypress interactive runner for component tests
npx cypress open --component
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

### Component Variants & States

Test how a component looks and behaves in different states (e.g., hover, disabled, loading, error). Use visual snapshots to capture each variant for regression testing.

**Testing button states:**
```typescript
describe("Button variants", () => {
  it("renders default state", () => {
    cy.mount(<Button>Click me</Button>);
    cy.compareSnapshot("button-default");
  });

  it("renders disabled state", () => {
    cy.mount(<Button disabled>Click me</Button>);
    cy.get("button").should("be.disabled");
    cy.compareSnapshot("button-disabled");
  });

  it("renders hover state", () => {
    cy.mount(<Button>Click me</Button>);
    cy.get("button").trigger("mouseover");
    cy.compareSnapshot("button-hover");
  });

  it("renders loading state", () => {
    cy.mount(<Button loading>Saving...</Button>);
    cy.get("button").should("be.disabled");
    cy.contains("Saving...").should("be.visible");
    cy.compareSnapshot("button-loading");
  });
});
```

**Testing card variants:**
```typescript
describe("Card variants", () => {
  it("renders default card", () => {
    cy.mount(<Card title="Default" description="Default state" />);
    cy.compareSnapshot("card-default");
  });

  it("renders error state", () => {
    cy.mount(<Card title="Error" error="Something went wrong" />);
    cy.contains("Something went wrong").should("be.visible");
    cy.compareSnapshot("card-error");
  });

  it("renders with different sizes", () => {
    cy.mount(<Card title="Small" size="sm" />);
    cy.compareSnapshot("card-small");
    
    cy.mount(<Card title="Large" size="lg" />);
    cy.compareSnapshot("card-large");
  });
});
```

**Testing modal states:**
```typescript
describe("Modal states", () => {
  it("renders closed modal", () => {
    cy.mount(<Modal isOpen={false}>Content</Modal>);
    cy.contains("Content").should("not.exist");
    cy.compareSnapshot("modal-closed");
  });

  it("renders open modal", () => {
    cy.mount(<Modal isOpen={true}>Content</Modal>);
    cy.contains("Content").should("be.visible");
    cy.compareSnapshot("modal-open");
  });
});
```

**Why test variants with snapshots:**
- Catches unintended visual changes across component states
- Documents expected appearance for each state
- Prevents regressions when refactoring component styles
- Makes state coverage explicit and reviewable

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

## Mandatory TDD Workflow for Component Tests

**Every new component MUST be developed using test-driven development.** A developer must write a part of the test, let it fail, then implement the part that is missing in the component. This cycle repeats until the component is complete.

### The TDD Cycle

```
Write Test → Run (Fails) → Implement Component Code → Run (Passes) → Repeat
```

### Step-by-Step Process

**Step 1: Write the component test first**

Before writing any component code, create the `.spec.tsx` file with the tests for the behavior you are about to implement.

```typescript
// src/components/NutritionResponse/NutritionResponse.spec.tsx
import { NutritionResponse } from "./NutritionResponse";

describe("NutritionResponse Component", () => {
  it("should render the introductory text", () => {
    cy.mount(<NutritionResponse data={MOCK_DATA} />);
    cy.contains("irregular meal timing").should("be.visible");
  });
});
```

**Step 2: Run the test — it MUST fail**

```bash
npx cypress run --component --spec "src/components/NutritionResponse/NutritionResponse.spec.tsx"
```

The test fails because the component does not exist yet. This confirms the test is valid and actually testing something.

**Step 3: Create the minimal component to make the test pass**

Write only enough code to pass the current test. Do not implement features that are not yet tested.

```tsx
// src/components/NutritionResponse/NutritionResponse.tsx
export function NutritionResponse({ data }: NutritionResponseProps) {
  return <div>{data.introText}</div>;
}
```

**Step 4: Run the test — it passes**

```bash
npx cypress run --component --spec "src/components/NutritionResponse/NutritionResponse.spec.tsx"
# 1 passing
```

**Step 5: Write the next test**

Add the next behavior you need to implement.

```typescript
it("should render exactly 3 numbered dietary adjustment cards", () => {
  cy.mount(<NutritionResponse data={MOCK_DATA} />);
  cy.contains("Time-restricted eating").should("be.visible");
  cy.contains("Protein-first meals").should("be.visible");
  cy.contains("Eliminate liquid calories").should("be.visible");
});
```

**Step 6: Run — it fails. Implement. Run — it passes. Repeat.**

Continue this cycle for every piece of functionality:
- Tip card rendering
- Physician card rendering
- Follow-up chip rendering
- Callback firing (onChipSelect, onBookPhysician)
- Edge cases (missing physician, empty tips)

### Rules

1. **Never write component code without a failing test first.** If there is no test for it, it does not exist.
2. **Write the minimum code to pass the current test.** Do not over-implement.
3. **Each test must fail before you fix it.** If a new test passes immediately, the test is not testing anything new — rewrite it.
4. **Commit tests and implementation together.** Each commit should contain both the test and the code that makes it pass.
5. **Component tests live alongside the component** in the same directory with `.spec.tsx` extension.

### Example: Full TDD Session for a TipCard Component

```
1. Write test: "should render tip number badge" → FAIL (file doesn't exist)
2. Create TipCard.tsx with minimal markup → PASS
3. Write test: "should render tip title" → FAIL
4. Add title rendering to TipCard → PASS
5. Write test: "should render tip description" → FAIL
6. Add description rendering → PASS
7. Write test: "should have aria-posinset for accessibility" → FAIL
8. Add aria attributes → PASS
9. Write test: "should apply custom className" → FAIL
10. Add cn() className support → PASS
```

---

## Component-Level vs Integration Testing

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

## Troubleshooting

### Placeholder Text Assertion

`cy.contains()` looks for visible text nodes, not placeholder attributes.

```typescript
// WRONG: cy.contains() looks for visible text nodes
cy.contains("Ask about nutrition, exercise, finding a doctor...").should("be.visible");

// CORRECT: Check the placeholder attribute
cy.get('input[placeholder*="Ask about nutrition"]').should("be.visible");
```

### Cypress Version Compatibility

Cypress 13+ uses `cypress/react` for component mounting. The old `cypress/react18` import does not exist and will cause:

```
"./react18" is not exported under the conditions ["module", "browser", "development", "import"]
from package node_modules/cypress
```

**Fix:** Use `import { mount } from "cypress/react"` in `cypress/support/component.ts`.

### Component Test Fails with "data-cy-root" Error

If you see an error about `component-index.html` not found, create `cypress/support/component-index.html`:

```html
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1.0" />
    <title>Components App</title>
  </head>
  <body>
    <div data-cy-root></div>
  </body>
</html>
```

---

## Quick Reference Card

| **Do** | **Don't** |
|--------|-----------|
| Use `.spec.tsx` for component tests | Use `.cy.tsx` (wrong extension) |
| Use `cy.mount()` for component tests | Use `cy.visit()` for component tests |
| Write tests BEFORE component code | Write component code first, tests after |
| Let each new test FAIL before implementing | Skip the failing step |
| Use semantic selectors (`aside`, `main`, class names) | Rely on `data-testid` (not used in this project) |
| Use `cy.get('input[placeholder*="..."]')` | Use `cy.contains()` for placeholder text |
| Import from `cypress/react` | Import from `cypress/react18` |
| Keep tests independent with `beforeEach` | Share state between tests |
| Use `cy.stub().as("name")` for callbacks | Test callbacks by checking DOM only |
| Test component variants & states with snapshots | Skip testing hover/disabled/loading states |
| Use `cy.compareSnapshot("name-state")` for variants | Use vague snapshot names like `"button-1"` |
