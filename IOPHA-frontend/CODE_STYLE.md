# Code Style Guide

This document defines style rules for the IOPHA frontend. Adhere to these patterns to pass linting, avoid runtime bugs, and keep state management maintainable.

## Table of Contents

1. [Component Props: `type` vs `interface`](#1-component-props-type-vs-interface)
2. [State Objects: Extract String Literals with `as const`](#2-state-objects-extract-string-literals-with-as-const)
3. [Validation Messages: Extract Repeated Error Strings](#3-validation-messages-extract-repeated-error-strings)
4. [Tailwind Class Strings: Extract Repeated Utility Classes](#4-tailwind-class-strings-extract-repeated-utility-classes)
5. [Safe Command Execution (Node `child_process`)](#5-safe-command-execution-node-child_process)
6. [Quick Reference](#6-quick-reference)

---

## 1. Component Props: `type` vs `interface`

### Rule

Use `type` for component prop definitions. Do not use an empty `interface`.

### Why

An empty `interface` that only extends an existing type is redundant. TypeScript allows multiple `interface` declarations to merge, which can cause accidental overwrites. A `type` alias is a single, non-mergable declaration that clearly signals "this is a type alias, not an open-ended contract."

Additionally, ESLint rule `@typescript-eslint/no-empty-object-type` enforces this because an empty object type provides no value over its supertype.

### Modern Best Practice: `React.ComponentProps<"input">`

For standard HTML elements, the modern React best practice is to use `React.ComponentProps<"input">` directly in the `forwardRef` generic. This avoids creating any intermediate type alias and automatically includes all standard HTML attributes, ARIA attributes, and React-specific props.

```tsx
const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
          className,
        )}
        ref={ref}
        {...props}
      />
    );
  },
);
```

### Acceptable Shortcut: Inline Type Alias

If you prefer to keep a named type alias for readability, define it directly without an empty interface:

```tsx
// CORRECT
export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return <input className={cn(className)} ref={ref} {...props} />;
  },
);

// INCORRECT
export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}
```

### Why the empty interface is wrong

The ESLint rule `@typescript-eslint/no-empty-object-type` flags this because an interface that only extends another type and adds no new properties is functionally identical to just using the supertype:

1. **Redundancy:** `interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}` adds no new fields, methods, or constraints.
2. **Cognitive overhead:** When another developer sees `InputProps`, they have to hunt down its definition only to realize it is just an empty alias.
3. **Type system bloat:** TypeScript is designed to handle type intersections and extensions natively. Creating empty interfaces clutters the module namespace with useless type aliases.

### When to Use `interface`

Use `interface` only when you need declaration merging (e.g., extending a global type across modules) or when defining an object type that will be implemented by classes.

---

## 2. State Objects: Extract String Literals with `as const`

### Rule

When a component manages view-state or mode-state using string literals, group those values into a single `as const` object and reference the object properties everywhere. Never scatter the same string literal across `setState`, `if` checks, and conditional renders.

### Why

This pattern satisfies `sonarjs/no-duplicate-string`, prevents typos from causing runtime bugs, and makes state transitions self-documenting.

### Implementation

**1. Define the constant at the top of the file (or in a shared constants file):**

```tsx
export const BOOKING_VIEWS = {
  CHAT: "chat",
  TIME_SELECTION: "time-selection",
  CONFIRMATION: "confirmation",
  SUCCESS: "success",
} as const;
```

**2. Derive the state type from the constant:**

```tsx
export type BookingViewType =
  (typeof BOOKING_VIEWS)[keyof typeof BOOKING_VIEWS];
```

**3. Use the constant in state and all transitions:**

```tsx
const [bookingView, setBookingView] = useState<BookingViewType>(
  BOOKING_VIEWS.CHAT,
);

setBookingView(BOOKING_VIEWS.TIME_SELECTION);
setBookingView(BOOKING_VIEWS.CONFIRMATION);
setBookingView(BOOKING_VIEWS.SUCCESS);

if (bookingView === BOOKING_VIEWS.TIME_SELECTION && selectedPhysician) {
  // render TimeSelector
}

if (
  bookingView === BOOKING_VIEWS.CONFIRMATION &&
  selectedPhysician &&
  selectedDate &&
  selectedTime
) {
  // render ConfirmationForm
}
```

### What Triggers This Rule

If `sonarjs/no-duplicate-string` flags a string literal appearing 3 or more times in the same file, extract it into a `as const` object. Common culprits:

- View-state strings (`"chat"`, `"time-selection"`, `"confirmation"`, `"success"`)
- Log message prefixes (`"[ChatArea] Booking initiated"`)
- CSS class names used in logic

### Benefits

| Benefit                | Explanation                                                                  |
| ---------------------- | ---------------------------------------------------------------------------- |
| Single source of truth | Change the value once; all references update                                 |
| Zero-cost type safety  | Typos in property names cause TypeScript errors; typos in raw strings do not |
| Self-documenting       | `BOOKING_VIEWS.TIME_SELECTION` is clearer than `"time-selection"`            |
| CI green               | Satisfies `sonarjs/no-duplicate-string` without file-level disables          |

---

## 3. Validation Messages: Extract Repeated Error Strings

### Rule

When the same validation or error message string is reused 3 or more times in a file (common in Zod schemas, form validation, or toast notifications), extract it into a named constant. Do not scatter magic strings throughout validation logic.

### Why

This satisfies `sonarjs/no-duplicate-string` and makes the codebase ready for future i18n.

### Implementation

**1. Define the constant at the top of the file:**

```tsx
const REQUIRED_FIELD_ERROR = "This field is required";
```

**2. Reference it in your validation schema:**

```tsx
const validationSchema = z.object({
  name: z.string().min(1, REQUIRED_FIELD_ERROR),
  email: z
    .string()
    .min(1, REQUIRED_FIELD_ERROR)
    .email("Please enter a valid email address"),
  phone: z
    .string()
    .min(1, REQUIRED_FIELD_ERROR)
    .regex(/^\d{10}$/, "Please enter a valid 10-digit phone number"),
  reason: z.string().optional(),
});
```

### Alternative: Zod Built-ins

If you use `.min(1)` solely to prevent empty strings, Zod offers `.nonempty()` as a cleaner alias:

```tsx
z.string().nonempty(REQUIRED_FIELD_ERROR);
```

This is functionally identical to `.min(1, message)` but more semantically accurate.

### What Triggers This Rule

- Validation strings duplicated across fields in the same file
- Error messages hardcoded in multiple `if` branches or `switch` cases
- Toast notification labels repeated in different handlers

### Benefits

| Benefit                | Explanation                                                               |
| ---------------------- | ------------------------------------------------------------------------- |
| Single source of truth | Product updates copy once; UI updates everywhere                          |
| Prevents typos         | `REQUIRED_FIELD_ERROR` is checked by TS; `"This field is requred"` is not |
| i18n-ready             | Centralized strings are trivial to replace with translation keys          |
| CI green               | Satisfies `sonarjs/no-duplicate-string`                                   |

---

## 4. Tailwind Class Strings: Extract Repeated Utility Classes

### Rule

When the same long Tailwind class string is copy-pasted 3 or more times in a file (common in form input error styles, button variants, card layouts), extract it into a named constant at the top of the file.

### Why

This satisfies `sonarjs/no-duplicate-string` and makes JSX readable. If your design system changes a color or spacing value, you update the constant once.

### Implementation

**1. Define the constants at the top of the file:**

```tsx
const DEFAULT_INPUT_CLASSES =
  "border-blue-600 focus:border-blue-600 focus-visible:border-blue-600 focus:ring-blue-600/50 focus-visible:ring-blue-600/50 focus:!outline-none";

const ERROR_INPUT_CLASSES =
  "border-destructive focus:border-destructive focus-visible:border-destructive focus:ring-destructive/20 focus-visible:ring-destructive/20";
```

**2. Reference them in your `cn()` calls:**

```tsx
<Input
  className={cn(DEFAULT_INPUT_CLASSES, errors.name && ERROR_INPUT_CLASSES)}
/>
```

### What Triggers This Rule

- Input error styles repeated across multiple fields in the same form
- Button variant classes repeated across multiple buttons
- Card layout classes repeated across multiple cards

### Benefits

| Benefit                | Explanation                                     |
| ---------------------- | ----------------------------------------------- |
| Single source of truth | Design updates propagate everywhere             |
| Cleaner JSX            | Logic is visible; 200-character strings are not |
| CI green               | Satisfies `sonarjs/no-duplicate-string`         |

---

## 5. Safe Command Execution (Node `child_process`)

### Rule

Never interpolate variables into a shell command string with `execSync` / `exec`. Always use `execFileSync` (or `spawn` / `execFile`) and pass the command and its arguments as a **separate array**.

### Why

Interpolating variables into a command string runs the command through a shell (`/bin/sh -c`). That is both fragile and dangerous:

1. **Shell injection:** If a variable (a file path, branch name, or any external input) contains shell metacharacters (`;`, `&&`, `$()`, backticks), an attacker can execute arbitrary commands.
2. **Breaks on spaces / special chars:** A path such as `My Component.spec.tsx` is word-split by the shell, silently breaking the command.
3. **Quote hell:** Embedded quotes (e.g. `'npx cypress run --e2e'`) are easy to get wrong and are still subject to the above.

Passing an arguments array bypasses the shell entirely. The OS passes each array element as a single, discrete argument, so special characters are handled literally and no shell parsing occurs.

### Implementation

```js
// INCORRECT — runs through a shell; vulnerable to injection and word-splitting
execSync(`npx cypress run --component --headless --spec "${specList}"`, {
  cwd: FRONTEND_DIR,
  stdio: "inherit",
});

// CORRECT — no shell; specList reaches Cypress as one argument
execFileSync(
  "npx",
  ["cypress", "run", "--component", "--headless", "--spec", specList],
  { cwd: FRONTEND_DIR, stdio: "inherit" },
);
```

Even a comma-separated value such as `"src/a.spec.ts,src/b.spec.ts"` is safe: as a single array element it reaches the program untouched, and the program parses the comma list itself. The same pattern applies to fixed commands — prefer `execFileSync("git", ["diff", "--name-only", "main...HEAD"], { ... })` over `execSync("git diff ...")`.

### What Triggers This Rule

- Any `execSync(` / `exec(` call whose string contains a `${...}` interpolation.
- Any command string containing embedded quotes or multiple space-separated subcommands.
- ESLint surfaces this via `security/detect-child-process`; the Python equivalent is Ruff `S602`/`S604`/`S605`/`S607`.

### Benefits

| Benefit         | Explanation                                         |
| --------------- | --------------------------------------------------- |
| Injection-proof | No shell is spawned, so metacharacters are inert    |
| Robust paths    | Files with spaces/quotes are passed verbatim        |
| Predictable     | Arguments map 1:1 to `argv`, with no word-splitting |
| CI green        | Satisfies `security/detect-child-process`           |

---

## 6. Quick Reference

| Violation                                                | Fix                                                                                      |
| -------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Empty `interface Props extends SomeType {}`              | Change to `type Props = SomeType;`                                                       |
| String literal used 3+ times                             | Extract to `const OBJECT = { KEY: "value" } as const;`                                   |
| Magic string in `setState` / `if` / `switch`             | Replace with constant property reference                                                 |
| Duplicated validation message                            | Extract to `const ERROR_MESSAGE = "text";` and reuse                                     |
| Duplicated Tailwind class string                         | Extract to `const CLASS_NAME = "..."` and reuse                                          |
| Unused manual union type when derived type exists        | Delete the manual type; use `type Name = typeof CONSTANT[keyof typeof CONSTANT]` instead |
| Variable interpolated into `execSync(...)` / `exec(...)` | Use `execFileSync(cmd, [args...])` with a discrete args array (no shell)                 |
