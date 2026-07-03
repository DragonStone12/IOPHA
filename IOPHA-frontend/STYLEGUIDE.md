# IOPHA Frontend Style Guide

## Border Styling Patterns

### Circular Borders

When creating circular elements with borders, the `rounded-full` class must be on the **same element** that receives the border classes.

```tsx
// Correct: rounded-full and border on same element
<button className="h-9 w-9 rounded-full border-2 border-blue-600">
  8
</button>

// Wrong: border on parent, rounded-full on child
<div className="h-9 w-9 border-2 border-blue-600">  // square border
  <span className="rounded-full">8</span>
</div>
```

### Focus State Borders

Always pair border color changes with `outline-none` to suppress the browser's native focus ring, which otherwise renders as a thick blue square around your element.

```tsx
// Correct pattern
<Input
  className={cn(
    "border-blue-600",
    "focus:border-blue-600 focus:ring-blue-600/50",
    "focus:outline-none"
  )}
/>

// Wrong: browser outline will override your ring
<Input className="border-blue-600 focus:ring-blue-600/50" />
```

### Keyboard vs Mouse Focus

Use `focus-visible:` for keyboard-only focus indication and `focus:` for all focus states. The base layer in `index.css` applies `outline-ring/50` globally via `@layer base { * { @apply outline-ring/50 } }`, which has higher specificity than utility classes. Use `!` to override when needed:

```tsx
// Suppresses outline on both mouse and keyboard
className = "focus:!outline-none";

// Keeps visible ring for keyboard users only
className = "outline-none focus-visible:ring-2 focus-visible:ring-blue-400";
```

---

## react-day-picker v10 Styling

### The `group` + `group-aria-selected` Pattern

In react-day-picker v10, the `aria-selected="true"` attribute is applied to the **parent `<td>`** element (the `day`), not the `<button>` inside it (the `day_button`). To style the button based on selection state, use Tailwind's group utilities:

```tsx
<DayPicker
  classNames={{
    // Parent gets 'group' marker
    day: "h-9 w-9 p-0 group",

    // Child uses group-aria-selected: variants
    day_button:
      "h-9 w-9 rounded-full font-normal cursor-pointer transition-colors " +
      "outline-none focus-visible:ring-2 focus-visible:ring-blue-400 " +
      "group-aria-selected:border-2 group-aria-selected:border-blue-600 " +
      "group-aria-selected:bg-blue-50 group-aria-selected:font-semibold",
  }}
/>
```

### Why `modifiersClassNames` Doesn't Work Here

`modifiersClassNames.selected` applies classes to the `day` cell (`<td>`), not the button. Since the button has `rounded-full` and the `<td>` does not, borders applied via `modifiersClassNames` render as squares.

### Why `aria-selected:` Variant Doesn't Work

The `aria-selected:` Tailwind variant matches the attribute on the **same element**. Since the button never has `aria-selected`, `aria-selected:border-2` on `day_button` does nothing.

### Testing Selected State

Don't test for `.rdp-day_selected` class names — they may not exist when you override `classNames`. Instead, assert against the stable attribute and computed styles:

```tsx
// Correct: tests what the user actually sees
cy.get('td[aria-selected="true"] button')
  .should("have.css", "border-width", "2px")
  .and("have.css", "border-color", "rgb(37, 99, 235)")
  .and("have.css", "border-radius", "9999px");

// Wrong: tests implementation details that may change
cy.get(".rdp-day_selected").should("have.class", "border-2");
```

---

## Form Autocomplete Suppression

### Why `autoComplete="off"` Fails

Modern browsers (especially Chrome) aggressively ignore `autoComplete="off"` on name, email, and phone fields. They use heuristics based on `name` attributes, label text, and field position.

### The Two-Part Solution

**1. Hidden dummy fields** — Place at the top of the form to intercept browser autofill:

```tsx
<form autoComplete="off">
  <input
    type="text"
    name="fake_user_name"
    autoComplete="username"
    className="hidden"
    tabIndex={-1}
    aria-hidden="true"
  />
  <input
    type="password"
    name="fake_password"
    autoComplete="new-password"
    className="hidden"
    tabIndex={-1}
    aria-hidden="true"
  />
  {/* Real fields follow */}
</form>
```

**2. `autoComplete="new-password"`** — On actual inputs, this is the most reliable bypass for Chrome:

```tsx
<Input
  id="patient-name"
  name="patient_name"
  autoComplete="new-password"
  // ...
/>
```

### Why This Combination Works

- The hidden `username` field satisfies the browser's expectation for a username field
- The hidden `new-password` field satisfies the expectation for a password field
- Real fields with `new-password` tell the browser "this is not a credential field"
- Using `className="hidden"` (Tailwind) instead of `style={{ display: 'none' }}` keeps them in the DOM but invisible

---

## twMerge Class Conflict Resolution

### How `cn()` Works

The `cn()` utility uses `twMerge` to resolve Tailwind class conflicts. It understands Tailwind's class groups and merges them intelligently:

```tsx
// twMerge knows border-blue-600 overrides border-input
cn("border-input", "border-blue-600"); // => "border-blue-600"

// twMerge knows focus:border-blue-600 overrides focus:border-ring
cn("focus:border-ring", "focus:border-blue-600"); // => "focus:border-blue-600"
```

### CSS Selectors Don't Merge

CSS selectors like `[&_input]:focus-visible:border-blue-500` are not Tailwind utility classes. `twMerge` cannot resolve conflicts between them and utility classes. Always pass focus variants directly on the component:

```tsx
// Wrong: twMerge can't resolve this
<form className="[&_input]:focus-visible:border-blue-500">
  <Input className="focus-visible:border-ring" />  // ring wins
</form>

// Correct: twMerge resolves this
<Input className="focus-visible:border-ring focus-visible:border-blue-600" />  // blue wins
```

### Error State Pattern

When an input has both a default focus style and an error focus style, include both `focus:` and `focus-visible:` variants in the error condition:

```tsx
className={cn(
  "border-blue-600 focus:border-blue-600 focus-visible:border-blue-600",
  errors.name && "border-destructive focus:border-destructive focus-visible:border-destructive",
)}
```

---

## Gotchas Summary

| Symptom                                      | Cause                                                      | Fix                                            |
| -------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------- |
| Blue square around selected date             | Browser native `outline` from base layer                   | `focus:!outline-none` on day + day_button      |
| Square border instead of circle              | `border` on parent, `rounded-full` on child                | Put both on same element                       |
| Teal ring instead of blue on input focus     | `focus-visible:border-ring` from Input base not overridden | Pass `focus:border-blue-600` directly on Input |
| `group-aria-selected:` not working           | `group` missing from parent element                        | Add `group` to `day` classNames                |
| `aria-selected:` variant not working         | Attribute is on parent, not button                         | Use `group-aria-selected:` instead             |
| `modifiersClassNames` renders square         | Classes applied to `<td>`, not `<button>`                  | Use `group-aria-selected:` on `day_button`     |
| Autocomplete still appears                   | `autoComplete="off"` ignored by Chrome                     | Hidden dummy fields + `new-password`           |
| CSS selector focus styles not applying       | `twMerge` can't resolve CSS selectors                      | Pass variants directly on component            |
| `focus:outline-none` not suppressing outline | Base layer `@apply outline-ring/50` has higher specificity | Use `focus:!outline-none`                      |

---

## Quick Reference

### Calendar Selected State

```tsx
day: "h-9 w-9 p-0 group",
day_button:
  "h-9 w-9 rounded-full " +
  "outline-none focus-visible:ring-2 focus-visible:ring-blue-400 " +
  "group-aria-selected:border-2 group-aria-selected:border-blue-600 " +
  "group-aria-selected:bg-blue-50 group-aria-selected:font-semibold",
```

### Input with Blue Border

```tsx
<Input
  className={cn(
    "border-blue-600",
    "focus:border-blue-600 focus-visible:border-blue-600",
    "focus:ring-blue-600/50 focus-visible:ring-blue-600/50",
    "focus:outline-none",
  )}
/>
```

### Autocomplete-Suppressed Form

```tsx
<form autoComplete="off">
  <input
    type="text"
    name="fake_user_name"
    autoComplete="username"
    className="hidden"
    tabIndex={-1}
    aria-hidden="true"
  />
  <input
    type="password"
    name="fake_password"
    autoComplete="new-password"
    className="hidden"
    tabIndex={-1}
    aria-hidden="true"
  />
  <Input name="patient_name" autoComplete="new-password" />
</form>
```
