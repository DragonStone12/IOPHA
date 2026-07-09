# ESLint Security & Bug Detection

## Table of Contents

| #   | Section                                     | Description                               |
| --- | ------------------------------------------- | ----------------------------------------- |
| 1   | [Overview](#overview)                       | Threat categories and scope               |
| 2   | [Plugin Breakdown](#plugin-breakdown)       | Detailed rules for each plugin            |
| 3   | [Configuration](#configuration)             | Rule overrides and file-specific settings |
| 4   | [CI Integration](#ci-integration)           | Pre-push hook, GitHub Actions, SARIF      |
| 5   | [Handling Violations](#handling-violations) | Inline disables, tuning, adding rules     |
| 6   | [Complementary Tools](#complementary-tools) | Defense-in-depth tooling                  |

## Overview

The IOPHA frontend uses ESLint as its primary static analysis tool. Beyond baseline code style and TypeScript type-checking, a dedicated set of plugins scans for security vulnerabilities, unstable patterns, and logic bugs before code reaches production. These checks run on every push via the Husky pre-push hook and on every pull request via GitHub Actions.

### What This Guards Against

| Threat Category                     | What It Catches                                                                                 |
| ----------------------------------- | ----------------------------------------------------------------------------------------------- |
| **Code injection**                  | Dynamic `eval()`, untrusted string execution                                                    |
| **Filesystem abuse**                | Non-literal `fs` paths that could traverse outside intended directories                         |
| **Child process injection**         | Unsanitized input passed to `exec`, `spawn`, `child_process`                                    |
| **Weak cryptography**               | Use of `Math.random()` or `crypto.pseudoRandomBytes` where cryptographic randomness is required |
| **Cross-site scripting (XSS)**      | Unsafe assignments to `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`          |
| **Hardcoded credentials**           | API keys, tokens, passwords, and private keys committed to source                               |
| **Logic bugs**                      | Duplicate strings, inverted boolean checks, unreachable branches, high cognitive complexity     |
| **Unhandled promises**              | Missing `.catch()`, nested promises, promises inside callbacks                                  |
| **Deprecated / missing APIs**       | Use of removed Node.js APIs, broken `require()` calls                                           |
| **Regex denial-of-service (ReDoS)** | Catastrophic backtracking, useless flags, inefficient patterns                                  |

---

## Plugin Breakdown

### 1. `eslint-plugin-security` — General JS/Node Security

**Focus:** Detects common security anti-patterns in JavaScript and Node.js code.

This plugin is the actively maintained fork of the archived `eslint-plugin-security` under the `@eslint-community` organization. It works with ESLint 8 and 9.

| Rule                                      | Severity  | What It Does                                                                                                                                              |
| ----------------------------------------- | --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `security/detect-eval-with-expression`    | **error** | Flags `eval()` calls where the argument is a variable or expression (not a string literal). Dynamic `eval` is the primary vector for code injection.      |
| `security/detect-non-literal-fs-filename` | **warn**  | Warns when `fs.readFile`, `fs.writeFile`, etc. receive a variable path instead of a literal. Prevents path traversal attacks.                             |
| `security/detect-child-process`           | **error** | Flags `child_process.exec`, `spawn`, `execSync` usage. Shell execution with untrusted input leads to command injection.                                   |
| `security/detect-pseudoRandomBytes`       | **warn**  | Warns on `Math.random()` and `crypto.pseudoRandomBytes`. These are not cryptographically secure and should not be used for tokens, session IDs, or salts. |

### 2. `eslint-plugin-no-secrets` — Hardcoded Credential Detection

**Focus:** Scans source code for accidentally committed secrets.

Uses regex patterns combined with entropy analysis to detect strings that look like API keys, passwords, tokens, and private keys. This catches common mistakes like hardcoding AWS keys or database passwords.

| Rule                    | Severity  | What It Does                                                                                                                                                                                        |
| ----------------------- | --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `no-secrets/no-secrets` | **error** | Detects high-entropy strings that match known secret patterns (API keys, tokens, passwords, private keys). Entropy threshold and pattern matching reduce false positives while catching real leaks. |

**Tuning:** The rule is disabled for test files (`cypress/**/*`, `**/*.spec.tsx`, `**/*.steps.ts`) because test fixtures often contain mock data that triggers false positives. Public URLs (e.g., Unsplash image links) that trigger entropy warnings are suppressed with inline `eslint-disable-next-line` comments.

### 3. `eslint-plugin-sonarjs` — Logic Bug & Maintainability Detection

**Focus:** Catches hidden logic bugs, code smells, and maintainability issues.

Powered by SonarQube's static analysis rules, this plugin identifies patterns that are technically valid JavaScript but indicate likely bugs or unmaintainable code.

| Rule                                 | Severity                    | What It Does                                                                                                                                     |
| ------------------------------------ | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `sonarjs/cognitive-complexity`       | **warn** (threshold: 15)    | Measures how hard a function is to understand. High complexity correlates with bug density. Functions exceeding 15 should be refactored.         |
| `sonarjs/no-duplicate-string`        | **warn**                    | Flags the same string literal used 3+ times. Duplicated strings should be extracted to named constants for maintainability and to prevent typos. |
| `sonarjs/no-all-duplicated-branches` | **error** (via recommended) | Detects `if/else` branches with identical bodies — a sign of copy-paste errors or dead logic.                                                    |
| `sonarjs/no-inverted-boolean-check`  | **warn** (via recommended)  | Flags double-negation boolean checks (`!!x === true`) that reduce readability.                                                                   |

### 4. `eslint-plugin-promise` — Async/Await Mistake Detection

**Focus:** Catches unhandled rejections and broken promise chains.

JavaScript's async/await syntax can mask error-handling gaps. This plugin ensures promises are properly chained and rejections are caught.

| Rule                             | Severity                   | What It Does                                                                                                                 |
| -------------------------------- | -------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `promise/catch-or-return`        | **error**                  | Requires every promise chain to end with `.catch()` or return the promise. Prevents unhandled rejection crashes.             |
| `promise/no-nesting`             | **warn**                   | Flags `.then()` callbacks that create new promises (promise nesting). Use `async/await` or flat chaining instead.            |
| `promise/always-return`          | **warn** (via recommended) | Ensures every `.then()` callback returns a value or promise. Missing returns break the chain silently.                       |
| `promise/no-promise-in-callback` | **warn** (via recommended) | Warns when promises are created inside Node-style callbacks. Mixing callback and promise patterns leads to unhandled errors. |

**Tuning:** Disabled for Cypress test files because Cypress's own API uses promise-like chains that don't follow standard promise conventions.

### 5. `eslint-plugin-n` — Node.js API Misuse Detection

**Focus:** Catches use of deprecated Node.js APIs and broken module resolution.

Official replacement for the deprecated `eslint-plugin-node`. Ensures code uses current, supported Node.js APIs.

| Rule                                      | Severity                 | What It Does                                                                                                                                              |
| ----------------------------------------- | ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `n/no-deprecated-api`                     | **error**                | Flags use of Node.js APIs that have been deprecated or removed. Prevents runtime crashes when upgrading Node versions.                                    |
| `n/no-missing-require`                    | **off**                  | Would flag `require()` calls for non-existent modules. Disabled because the project uses ESM imports, not CommonJS `require()`.                           |
| `n/no-unsupported-features/node-builtins` | **off** (for `.ts/.tsx`) | Would flag browser APIs like `fetch` as unsupported in older Node versions. Disabled for TypeScript files since frontend code runs in browsers, not Node. |

### 6. `eslint-plugin-regexp` — Regex Safety

**Focus:** Prevents catastrophic regex backtracking (ReDoS) and invalid patterns.

Regular expressions with super-linear backtracking can be exploited to cause denial-of-service attacks by feeding specially crafted input. This plugin catches those patterns at lint time.

| Rule                                  | Severity                   | What It Does                                                                                                                                                      |
| ------------------------------------- | -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | --- | -------------------------------------------------------------------------- |
| `regexp/no-super-linear-backtracking` | **error**                  | Detects regex patterns with nested quantifiers (e.g., `(a+)+`) that exhibit catastrophic backtracking. These patterns can hang the event loop on malicious input. |
| `regexp/no-useless-flag`              | **warn**                   | Flags regex flags that have no effect (e.g., `g` on a pattern used with `.test()`). Useless flags indicate misunderstandings about regex behavior.                |
| `regexp/prefer-character-class`       | **warn** (via recommended) | Suggests `[abc]` over `a                                                                                                                                          | b   | c` for single-character alternation. Improves readability and performance. |

---

## Configuration

All plugins are configured in `IOPHA-frontend/.eslintrc.cjs`. The configuration extends each plugin's recommended preset and adds project-specific rule overrides.

### Rule Overrides

```javascript
rules: {
  // Security
  "security/detect-eval-with-expression": "error",
  "security/detect-non-literal-fs-filename": "warn",
  "security/detect-child-process": "error",
  "security/detect-pseudoRandomBytes": "warn",
  "no-secrets/no-secrets": "error",

  // Bug detection
  "sonarjs/cognitive-complexity": ["warn", 15],
  "sonarjs/no-duplicate-string": "warn",
  "promise/catch-or-return": "error",
  "promise/no-nesting": "warn",
  "n/no-deprecated-api": "error",
  "n/no-missing-require": "off",
  "regexp/no-super-linear-backtracking": "error",
  "regexp/no-useless-flag": "warn",
}
```

### File-Specific Overrides

| File Pattern                                     | Disabled Rules                                                                                          | Reason                                                                                                |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `**/*.ts`, `**/*.tsx`                            | `n/no-missing-import`, `n/no-unsupported-features/es-syntax`, `n/no-unsupported-features/node-builtins` | Frontend code runs in browsers, not Node. Browser APIs like `fetch` and ESM imports are valid.        |
| `cypress/**/*`, `**/*.spec.tsx`, `**/*.steps.ts` | `no-secrets/no-secrets`, `promise/catch-or-return`, `sonarjs/no-duplicate-string`                       | Test fixtures contain mock data that triggers false positives. Cypress uses its own promise-like API. |

---

## CI Integration

### Pre-Push Hook

The Husky pre-push hook (`/.husky/pre-push`) runs lint before any push:

```bash
cd IOPHA-frontend && npm run lint && npm run cy:check-steps && npm run test:e2e && npx cypress run --component && npm audit --omit=dev --audit-level=high
```

`npm run lint` executes `eslint src --ext .ts,.tsx --max-warnings=0`, which fails the push if any security or bug rule triggers.

### GitHub Actions

The `ci-frontend.yml` workflow runs ESLint on every push and pull request to `main`. In addition to the standard lint check, it generates a SARIF report and uploads it to the GitHub Security tab:

```yaml
- name: Generate ESLint SARIF
  if: always()
  run: |
    npx eslint src --ext .ts,.tsx --format @microsoft/eslint-formatter-sarif --output-file eslint-results.sarif || true

- name: Upload SARIF results
  if: always()
  uses: github/codeql-action/upload-sarif@v4
  with:
    sarif_file: IOPHA-frontend/eslint-results.sarif
    category: eslint-security-bug-analysis
```

This surfaces security findings directly in GitHub's code scanning alerts, enabling security teams to track and triage issues without leaving the platform.

### Strict Mode

CI uses `--max-warnings=0` so that **any** warning or error from these plugins fails the workflow. This ensures security and bug rules cannot be silently ignored.

---

## Handling Violations

### Intentional Patterns

When a security rule flags a pattern that is intentional and safe (e.g., a public image URL that triggers entropy detection), use an inline disable comment:

```typescript
// eslint-disable-next-line no-secrets/no-secrets
const imageUrl = "https://images.unsplash.com/photo-1559839734-...";
```

Keep the scope as narrow as possible — disable only the specific rule on the specific line, not the entire file.

### Tuning Thresholds

If a rule is too noisy for the project's current codebase, adjust the severity or threshold in `.eslintrc.cjs` rather than disabling the rule entirely:

```javascript
// Reduce complexity threshold from 15 to 20 for legacy code
"sonarjs/cognitive-complexity": ["warn", 20],
```

### Adding New Rules

When adding new rules from these plugins:

1. Set severity to `"warn"` first to assess impact
2. Review existing violations and fix or suppress intentionally
3. Upgrade to `"error"` once the codebase is clean
4. Update this documentation with the new rule

---

## Complementary Tools

ESLint catches code-level issues. It should be paired with:

| Tool               | Scope        | What ESLint Misses                                  |
| ------------------ | ------------ | --------------------------------------------------- |
| `npm audit`        | Dependencies | Known vulnerabilities in `node_modules`             |
| `trufflehog`       | Git history  | Secrets committed in past commits (even if deleted) |
| CodeQL             | Data flow    | Taint analysis across function boundaries           |
| `bandit` (backend) | Python code  | Backend-specific security patterns                  |

These tools run in parallel in CI and provide defense-in-depth coverage.
