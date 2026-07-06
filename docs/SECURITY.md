# Security Documentation

## Table of Contents

| # | Section | Description |
|---|---------|-------------|
| 1 | [Overview](#overview) | Security posture, compliance, and threat model |
| 2 | [Trust Boundaries & Data Classification](#trust-boundaries--data-classification) | PHI zones, encryption, and access controls |
| 3 | [Static Application Security Testing](#static-application-security-testing) | ESLint security plugins, SARIF integration, CI enforcement |
| 4 | [Dependency & Supply-Chain Security](#dependency--supply-chain-security) | `npm audit`, pre-push hooks, CI audit |
| 5 | [Kilo AI Code Reviews & Security Agent](#kilo-ai-code-reviews--security-agent) | AI-powered PR reviews, Dependabot triage, auto-remediation |
| 6 | [PII Handling in Frontend Flows](#pii-handling-in-frontend-flows) | Booking form, logging, and transport security |
| 7 | [Compliance & Regulatory](#compliance--regulatory) | HIPAA, TLS, and audit requirements |
| 8 | [Quick Reference](#quick-reference) | Commands and links |

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

**Never bypass hooks with `--no-verify` or any other mechanism. If a hook fails, resolve the underlying issue instead of bypassing it.

## Kilo AI Code Reviews & Security Agent

[Kilo Code](https://kilo.ai) is integrated into this repository via a GitHub App. It provides two automated security and quality services: **AI Code Reviews** on pull requests and a **Security Agent** that triages dependency vulnerabilities.

### AI Code Reviews

Kilo's Code Reviewer automatically analyzes every pull request opened or updated on `DragonStone12/IOPHA`. The agent uses the **Auto Frontier** AI model and is configured in **Strict** review style, which flags all potential issues and prioritizes quality and security.

| Setting | Value |
|---|---|
| AI Model | Auto Frontier |
| Review Style | Strict |
| PR Gate Threshold | Critical issues only |
| Trigger | PR opened, new commits pushed, PR reopened, draft marked ready |

**PR Gate Threshold** — When set to "Critical issues only", the Kilo review posts a failing status check on the PR if any critical-severity findings are detected. This blocks merging until the critical issues are resolved or the threshold is adjusted.

**Focus Areas** — The reviewer is configured to check all six focus areas:

| Focus Area | What It Catches |
|---|---|
| Security vulnerabilities | SQL injection, XSS, unsafe APIs, hardcoded secrets |
| Performance issues | N+1 queries, inefficient loops, unnecessary re-renders |
| Bug detection | Logic errors, edge cases, null handling |
| Code style | Formatting, naming conventions, consistency |
| Test coverage | Missing or inadequate tests for changed code |
| Documentation | Missing JSDoc, outdated comments |

The reviewer also respects the repository's `REVIEW.md` file, which provides domain-specific review guidance, severity calibration, and sub-agent routing instructions.

### Security Agent

The Kilo Security Agent syncs **GitHub Dependabot alerts** and performs AI-powered triage to determine whether each CVE is actually exploitable in this codebase. It operates in two phases:

1. **AI Triage** — Evaluates package, advisory, severity, and dependency context without opening the repository sandbox. Routes each finding to: *Safe to Dismiss*, *Needs Analysis*, or *Needs Review*.
2. **Sandbox Analysis** — For findings that need deeper investigation, the agent inspects actual repository usage, identifies relevant files and code paths, captures evidence, and recommends a fix.

| Setting | Value |
|---|---|
| Auto-analysis | Enabled — All severities |
| Auto-remediation | Enabled — All severities (opens PRs for eligible exploitable findings) |
| Finding notifications | Email on — High and above |
| SLA compliance | 100% (no assigned deadlines) |
| Codebase risk | 100% (0 open findings) |

**Analysis Outcomes** — Each security finding is classified into one of:

| Outcome | Meaning |
|---|---|
| Confirmed exploitable | The vulnerable code path is reachable in this codebase |
| Not exploitable | The vulnerable dependency is not used in an exploitable way |
| Needs your review | The agent could not determine exploitability automatically |
| Analysis not complete | Sandbox analysis has not yet run |
| No SLA deadline assigned | Finding is tracked but no remediation deadline is set |

**Auto-remediation** — When enabled for all severities, Kilo automatically opens a pull request with a suggested fix for every eligible exploitable finding. Duplicate PRs are suppressed. The finding is not closed until Dependabot reports it fixed or a user manually dismisses it.

**SLA Tracking** — Remediation deadlines can be set per severity level. The dashboard tracks whether findings are resolved within their deadlines and sends warning/breach notifications.

### How This Complements Existing Security Layers

| Layer | Tool | When It Runs |
|---|---|---|
| Local static analysis | ESLint + security plugins | Pre-commit (Husky) |
| Local dependency audit | `npm audit` | Pre-push (Husky) |
| CI static analysis | ESLint → SARIF → GitHub Code Scanning | GitHub Actions on push/PR |
| CI dependency audit | `npm audit --audit-level=high` | GitHub Actions on push/PR |
| **AI code review** | **Kilo Code Reviewer** | **On PR open/update** |
| **Dependency vulnerability triage** | **Kilo Security Agent** | **Continuous (Dependabot sync)** |
| **Auto-remediation PRs** | **Kilo Security Agent** | **When exploitable finding detected** |

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

### Prometheus Metrics Endpoint Security

The `/metrics` endpoint exposes internal application state, endpoint names, request patterns, and infrastructure details. It must not be exposed to the public internet or the external API Gateway.

| Control | Implementation |
|---|---|
| Network isolation | Block `/metrics` at the API Gateway / load balancer level |
| Internal access only | Accessible only by the internal Prometheus scraper |
| Cardinality protection | `handle_unhandled_paths=False` prevents high-cardinality metric explosion |
| Path grouping | `should_group_status_codes=True` and `should_ignore_untemplated=True` reduce metric cardinality |

**Risks of exposure**:
- Endpoint enumeration: Attackers can discover internal API routes and naming conventions
- Infrastructure fingerprinting: Response size, latency, and status code patterns reveal server architecture
- Cardinality DoS: If dynamic paths like `/api/providers/{provider_id}/slots` are not grouped, unique metric series can exhaust Prometheus memory

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
| Kilo Code Reviewer dashboard | AI PR reviews, focus areas, PR gate threshold |
| Kilo Security Agent dashboard | Dependabot alerts triage, SLA tracking, auto-remediation |

**Related Documentation:**
- [ESLint Security & Bug Detection](ESLINT_SECURITY_BUG_DETECTION.md)
- [SARIF Justification](security/SARIF_JUSTIFICATION.md)
- [Architecture](ARCHITECTURE.md)
- [Cypress Testing Guide](CYPRESS_TESTING.md)
- [Kilo Code Reviews Documentation](https://kilo.ai/docs/automate/code-reviews/overview)
- [Kilo Security Agent Documentation](https://kilo.ai/docs/deploy-secure/security-reviews)
