# Security Documentation

## Table of Contents

| # | Section | Description |
|---|---------|-------------|
| 1 | [Overview](#overview) | Security posture, compliance, and threat model |
| 2 | [Trust Boundaries & Data Classification](#trust-boundaries--data-classification) | PHI zones, encryption, and access controls |
| 3 | [Static Application Security Testing](#static-application-security-testing) | ESLint security plugins, SARIF integration, CI enforcement |
| 4 | [Dependency & Supply-Chain Security](#dependency--supply-chain-security) | `npm audit`, pre-push hooks, CI audit |
| 5 | [PII Handling in Frontend Flows](#pii-handling-in-frontend-flows) | Booking form, logging, and transport security |
| 6 | [Compliance & Regulatory](#compliance--regulatory) | HIPAA, TLS, and audit requirements |
| 7 | [Quick Reference](#quick-reference) | Commands and links |

## Overview

IOPHA handles Protected Health Information (PHI) and user credentials. Security is enforced across three layers:

1. **Static analysis** — ESLint security/bug plugins run on every push via Husky and CI.
2. **Dependency auditing** — `npm audit` blocks high-severity vulnerabilities.
3. **Runtime hardening** — TLS 1.3, JWT auth, AES-256 encryption at rest, and server-side sanitization.

All security findings are surfaced in GitHub Code Scanning via SARIF reports.

## Trust Boundaries & Data Classification

| Zone | Components | PHI Exposure | Security Controls |
|---|---|---|---|
| **Public Zone** | Static assets, CDN | None | WAF, CSP headers |
| **Private Zone** | API, Backend Services | Processed transiently | JWT auth, rate limiting |
| **HIPAA Boundary** | Database, S3, LLM | At rest / in transit | AES-256 encryption, TLS 1.3 |

**PHI Entry Points**: User-submitted health data enters via authenticated API endpoints. All PHI is encrypted at rest (AES-256) and in transit (TLS 1.3).

**Access Control**:
- Role-based auth (patient, admin)
- JWT with httpOnly cookies
- Refresh token rotation

**Transmission Security**:
- TLS 1.3 for all external connections
- HTTPS enforced in production

## Static Application Security Testing

The frontend uses ESLint as its primary static analysis tool. Beyond baseline code style and TypeScript type-checking, a dedicated set of plugins scans for security vulnerabilities, unstable patterns, and logic bugs before code reaches production.

### Threat Coverage

| Threat Category | What It Catches |
|---|---|
| **Code injection** | Dynamic `eval()`, untrusted string execution |
| **Filesystem abuse** | Non-literal `fs` paths that could traverse outside intended directories |
| **Child process injection** | Unsanitized input passed to `exec`, `spawn`, `child_process` |
| **Weak cryptography** | Use of `Math.random()` or `crypto.pseudoRandomBytes` where cryptographic randomness is required |
| **Cross-site scripting (XSS)** | Unsafe assignments to `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write` |
| **Hardcoded credentials** | API keys, tokens, passwords, and private keys committed to source |
| **Logic bugs** | Duplicate strings, inverted boolean checks, unreachable branches, high cognitive complexity |
| **Unhandled promises** | Missing `.catch()`, nested promises, promises inside callbacks |
| **Deprecated / missing APIs** | Use of removed Node.js APIs, broken `require()` calls |
| **Regex denial-of-service (ReDoS)** | Catastrophic backtracking, useless flags, inefficient patterns |

### Plugin Breakdown

#### 1. `eslint-plugin-security` — General JS/Node Security

Detects common security anti-patterns in JavaScript and Node.js code.

| Rule | Severity | What It Does |
|---|---|---|
| `security/detect-eval-with-expression` | **error** | Flags `eval()` calls where the argument is a variable or expression. Dynamic `eval` is the primary vector for code injection. |
| `security/detect-non-literal-fs-filename` | **warn** | Warns when `fs.readFile`, `fs.writeFile`, etc. receive a variable path. Prevents path traversal attacks. |
| `security/detect-child-process` | **error** | Flags `child_process.exec`, `spawn`, `execSync` usage. Shell execution with untrusted input leads to command injection. |
| `security/detect-pseudoRandomBytes` | **warn** | Warns on `Math.random()` and `crypto.pseudoRandomBytes`. These are not cryptographically secure. |

#### 2. `eslint-plugin-no-secrets` — Hardcoded Credential Detection

Uses regex patterns combined with entropy analysis to detect strings that look like API keys, passwords, tokens, and private keys.

| Rule | Severity | What It Does |
|---|---|---|
| `no-secrets/no-secrets` | **error** | Detects high-entropy strings matching known secret patterns. |

**Tuning**: Disabled for test files (`cypress/**/*`, `**/*.spec.tsx`, `**/*.steps.ts`) because test fixtures often trigger false positives.

#### 3. `eslint-plugin-sonarjs` — Logic Bug & Maintainability Detection

Powered by SonarQube's static analysis rules.

| Rule | Severity | What It Does |
|---|---|---|
| `sonarjs/cognitive-complexity` | **warn** (threshold: 15) | Measures how hard a function is to understand. High complexity correlates with bug density. |
| `sonarjs/no-duplicate-string` | **warn** | Flags the same string literal used 3+ times. |
| `sonarjs/no-all-duplicated-branches` | **error** | Detects `if/else` branches with identical bodies. |
| `sonarjs/no-inverted-boolean-check` | **warn** | Flags double-negation boolean checks. |

#### 4. `eslint-plugin-promise` — Async/Await Mistake Detection

Ensures promises are properly chained and rejections are caught.

| Rule | Severity | What It Does |
|---|---|---|
| `promise/catch-or-return` | **error** | Requires every promise chain to end with `.catch()` or return. |
| `promise/no-nesting` | **warn** | Flags `.then()` callbacks that create new promises. |
| `promise/always-return` | **warn** | Ensures every `.then()` callback returns a value. |
| `promise/no-promise-in-callback` | **warn** | Warns when promises are created inside Node-style callbacks. |

**Tuning**: Disabled for Cypress test files because Cypress's API uses promise-like chains.

#### 5. `eslint-plugin-n` — Node.js API Misuse Detection

Official replacement for the deprecated `eslint-plugin-node`.

| Rule | Severity | What It Does |
|---|---|---|
| `n/no-deprecated-api` | **error** | Flags use of deprecated or removed Node.js APIs. |

Disabled rules:
- `n/no-missing-require` — disabled because the project uses ESM imports.
- `n/no-unsupported-features/node-builtins` — disabled for `.ts/.tsx` since frontend code runs in browsers.

#### 6. `eslint-plugin-regexp` — Regex Safety

Prevents catastrophic regex backtracking (ReDoS) and invalid patterns.

| Rule | Severity | What It Does |
|---|---|---|
| `regexp/no-super-linear-backtracking` | **error** | Detects regex patterns with nested quantifiers that exhibit catastrophic backtracking. |
| `regexp/no-useless-flag` | **warn** | Flags regex flags that have no effect. |
| `regexp/prefer-character-class` | **warn** | Suggests `[abc]` over `a\|b\|c`. |

### CI Configuration

All plugins are configured in `IOPHA-frontend/.eslintrc.cjs`. CI uses `--max-warnings=0` so any warning or error fails the workflow.

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

SARIF uploads surface findings in GitHub's Security tab as actionable, assignable alerts.

### Handling Violations

**Intentional Patterns**: When a security rule flags a safe pattern, use a narrow inline disable:

```typescript
// eslint-disable-next-line no-secrets/no-secrets
const imageUrl = "https://images.unsplash.com/photo-1559839734-...";
```

**Tuning**: Adjust severity or threshold in `.eslintrc.cjs` before disabling entirely.

**Adding New Rules**:
1. Set severity to `"warn"` first
2. Review and fix existing violations
3. Upgrade to `"error"` once clean
4. Update this document

### Complementary Tools

| Tool | Scope | What ESLint Misses |
|---|---|---|
| `npm audit` | Dependencies | Known vulnerabilities in `node_modules` |
| `trufflehog` | Git history | Secrets committed in past commits |
| CodeQL | Data flow | Taint analysis across function boundaries |
| `bandit` (backend) | Python code | Backend-specific security patterns |

## Dependency & Supply-Chain Security

### npm Audit

Runs on every push via the Husky pre-push hook:

```bash
cd IOPHA-frontend && npm run lint && npm run cy:check-steps && npm run test:e2e && npx cypress run --component && npm audit --omit=dev --audit-level=high
```

`npm audit --omit=dev --audit-level=high` blocks pushes if high-severity vulnerabilities exist in production dependencies.

### Pre-Push Hook

`/.husky/pre-push` enforces:

1. ESLint with security/bug plugins (`--max-warnings=0`)
2. Cypress step definition duplicate check
3. E2E tests (Gherkin BDD)
4. Component tests
5. `npm audit` (high severity only)

**Never bypass hooks with `git push --no-verify`.** Bypassing causes CI build failures and blocks PR merges.

## PII Handling in Frontend Flows

### Booking Form

The booking confirmation form collects Name, Email, and Phone. Security controls:

- **HTTPS only**: All submissions use TLS 1.3
- **Server-side sanitization**: Inputs are sanitized on the backend
- **No client-side logging**: Form payloads are not logged to the browser console
- **Inline validation**: Errors display adjacent to fields without revealing sensitive data

### Chat & RAG Responses

- User health data sent to the RAG engine is transmitted over encrypted channels.
- LLM responses are sanitized before rendering to prevent injection.
- Chat history is stored server-side with encryption at rest.

## Compliance & Regulatory

### HIPAA Alignment

| Control | Implementation |
|---|---|
| Access Control (§164.308) | Role-based auth (patient, admin), JWT with httpOnly cookies |
| Audit Controls (§164.312) | Server-side logging of PHI access, immutable audit trails |
| Transmission Security (§164.312) | TLS 1.3 for all external connections |
| Storage Encryption | AES-256 at rest for database and S3 |
| Integrity Controls | SARIF + ESLint prevents code-level vulnerabilities |

### Security Audit

The pre-push hook runs `npm audit --omit=dev --audit-level=high`. Known high-severity dependency vulnerabilities block the push until resolved.

## Quick Reference

| Command | Purpose |
|---|---|
| `npm run lint` | ESLint with security + bug rules; `--max-warnings=0` |
| `npm run cy:check-steps` | Detect duplicate Cucumber step definitions |
| `npm run test:e2e` | Start dev server + run all E2E tests |
| `npm run cy:update-snapshots` | Update visual regression baselines |
| `npm audit --omit=dev --audit-level=high` | Audit dependencies for high-severity issues |

**Related Documentation:**
- [ESLint Security & Bug Detection](ESLINT_SECURITY_BUG_DETECTION.md)
- [SARIF Justification](security/SARIF_JUSTIFICATION.md)
- [Architecture](ARCHITECTURE.md)
- [Cypress Testing Guide](CYPRESS_TESTING.md)
