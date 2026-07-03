# Code Style Guide

This document defines style rules for the IOPHA frontend. Adhere to these patterns to pass linting, avoid runtime bugs, and keep state management maintainable.

## Table of Contents

1. [Component Props: `type` vs `interface`](#1-component-props-type-vs-interface)
2. [State Objects: Extract String Literals with `as const`](#2-state-objects-extract-string-literals-with-as-const)
3. [Quick Reference](#3-quick-reference)

---

## 1. Component Props: `type` vs `interface`

### Rule

Use `type` for component prop definitions. Do not use an empty `interface`.

### Why

An empty `interface` that only extends an existing type is redundant. TypeScript allows multiple `interface` declarations to merge, which can cause accidental overwrites. A `type` alias is a single, non-mergable declaration that clearly signals "this is a type alias, not an open-ended contract."

Additionally, ESLint rule `@typescript-eslint/no-empty-object-type` enforces this because an empty object type provides no value over its supertype.

### Example

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
export type BookingViewType = typeof BOOKING_VIEWS[keyof typeof BOOKING_VIEWS];
```

**3. Use the constant in state and all transitions:**

```tsx
const [bookingView, setBookingView] = useState<BookingViewType>(BOOKING_VIEWS.CHAT);

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

| Benefit | Explanation |
|---------|-------------|
| Single source of truth | Change the value once; all references update |
| Zero-cost type safety | Typos in property names cause TypeScript errors; typos in raw strings do not |
| Self-documenting | `BOOKING_VIEWS.TIME_SELECTION` is clearer than `"time-selection"` |
| CI green | Satisfies `sonarjs/no-duplicate-string` without file-level disables |

---

## 3. Quick Reference

| Violation | Fix |
|-----------|-----|
| Empty `interface Props extends SomeType {}` | Change to `type Props = SomeType;` |
| String literal used 3+ times | Extract to `const OBJECT = { KEY: "value" } as const;` |
| Magic string in `setState` / `if` / `switch` | Replace with constant property reference |
