# Security Documentation

## Table of Contents

| #   | Section                                                                          | Description                                                |
| --- | -------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| 1   | [Overview](#overview)                                                            | Security posture, compliance, and threat model             |
| 2   | [Trust Boundaries & Data Classification](#trust-boundaries--data-classification) | PHI zones, encryption, and access controls                 |
| 3   | [Static Application Security Testing](#static-application-security-testing)      | ESLint security plugins, SARIF integration, CI enforcement |
| 4   | [Dependency & Supply-Chain Security](#dependency--supply-chain-security)         | `npm audit`, pre-push hooks, CI audit                      |
| 5   | [Kilo AI Code Reviews & Security Agent](#kilo-ai-code-reviews--security-agent)   | AI-powered PR reviews, Dependabot triage, auto-remediation |
| 6   | [PII Handling in Frontend Flows](#pii-handling-in-frontend-flows)                | Booking form, logging, and transport security              |
| 7   | [Compliance & Regulatory](#compliance--regulatory)                               | HIPAA, TLS, and audit requirements                         |
| 8   | [Structured JSON Logging Compliance](#structured-json-logging-compliance)       | PHI prevention, aggregation security, audit trail         |
| 9   | [Sensitive Data Handling](SENSITIVE_DATA_HANDLING.md)                            | PHI/PII redaction architecture, credential scrubbing, and PHIScrubber idempotency fix |
| 10  | [Input Validation](INPUT_VALIDATION.md)                                          | API schema payload limits and DoS prevention               |
| 11  | [Quick Reference](#quick-reference)                                              | Commands and links                                         |

## Overview

IOPHA handles Protected Health Information (PHI) and user credentials. Security is enforced across three layers:

1. **Static analysis** — ESLint security/bug plugins run on every push via Husky and CI.
2. **Dependency auditing** — `npm audit` blocks high-severity vulnerabilities.
3. **Runtime hardening** — TLS 1.3, JWT auth, AES-256 encryption at rest, and server-side sanitization.

All security findings are surfaced in GitHub Code Scanning via SARIF reports.

## Trust Boundaries & Data Classification

| Zone               | Components            | PHI Exposure          | Security Controls           |
| ------------------ | --------------------- | --------------------- | --------------------------- |
| **Public Zone**    | Static assets, CDN    | None                  | WAF, CSP headers            |
| **Private Zone**   | API, Backend Services | Processed transiently | JWT auth, rate limiting     |
| **HIPAA Boundary** | Database, S3, LLM     | At rest / in transit  | AES-256 encryption, TLS 1.3 |

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

### Backend Static Analysis

The backend uses Ruff and Mypy for static analysis:

| Tool | Rules                    | Purpose                                                                                   |
| ---- | ------------------------ | ----------------------------------------------------------------------------------------- |
| Ruff | E, F, I, N, W, S, B, PLR | Linting (pycodestyle, pyflakes, isort, pydocstyle, bandit security, bugbear, refactoring) |
| Mypy | Strict mode              | Static type checking with warning flags                                                   |

**Ruff Security Rules (S)**: Bandit-compatible security checks including:

- S101: `assert` used for runtime guarantees (bypassed in tests)
- S105: Hardcoded password strings (ignored)
- S106: Hardcoded password function arguments (ignored)
- S107: Hardcoded password method call (ignored)

**Bugbear Rules (B)**: Catch common bugs and design problems in Python code.

**Pylint Refactoring Rules (PLR)**: Code complexity and maintainability checks.

### Threat Coverage

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

### Plugin Breakdown

#### 1. `eslint-plugin-security` — General JS/Node Security

Detects common security anti-patterns in JavaScript and Node.js code.

| Rule                                      | Severity  | What It Does                                                                                                                  |
| ----------------------------------------- | --------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `security/detect-eval-with-expression`    | **error** | Flags `eval()` calls where the argument is a variable or expression. Dynamic `eval` is the primary vector for code injection. |
| `security/detect-non-literal-fs-filename` | **warn**  | Warns when `fs.readFile`, `fs.writeFile`, etc. receive a variable path. Prevents path traversal attacks.                      |
| `security/detect-child-process`           | **error** | Flags `child_process.exec`, `spawn`, `execSync` usage. Shell execution with untrusted input leads to command injection.       |
| `security/detect-pseudoRandomBytes`       | **warn**  | Warns on `Math.random()` and `crypto.pseudoRandomBytes`. These are not cryptographically secure.                              |

#### 2. `eslint-plugin-no-secrets` — Hardcoded Credential Detection

Uses regex patterns combined with entropy analysis to detect strings that look like API keys, passwords, tokens, and private keys.

| Rule                    | Severity  | What It Does                                                 |
| ----------------------- | --------- | ------------------------------------------------------------ |
| `no-secrets/no-secrets` | **error** | Detects high-entropy strings matching known secret patterns. |

**Tuning**: Disabled for test files (`cypress/**/*`, `**/*.spec.tsx`, `**/*.steps.ts`) because test fixtures often trigger false positives.

#### 3. `eslint-plugin-sonarjs` — Logic Bug & Maintainability Detection

Powered by SonarQube's static analysis rules.

| Rule                                 | Severity                 | What It Does                                                                                |
| ------------------------------------ | ------------------------ | ------------------------------------------------------------------------------------------- |
| `sonarjs/cognitive-complexity`       | **warn** (threshold: 15) | Measures how hard a function is to understand. High complexity correlates with bug density. |
| `sonarjs/no-duplicate-string`        | **warn**                 | Flags the same string literal used 3+ times.                                                |
| `sonarjs/no-all-duplicated-branches` | **error**                | Detects `if/else` branches with identical bodies.                                           |
| `sonarjs/no-inverted-boolean-check`  | **warn**                 | Flags double-negation boolean checks.                                                       |

#### 4. `eslint-plugin-promise` — Async/Await Mistake Detection

Ensures promises are properly chained and rejections are caught.

| Rule                             | Severity  | What It Does                                                   |
| -------------------------------- | --------- | -------------------------------------------------------------- |
| `promise/catch-or-return`        | **error** | Requires every promise chain to end with `.catch()` or return. |
| `promise/no-nesting`             | **warn**  | Flags `.then()` callbacks that create new promises.            |
| `promise/always-return`          | **warn**  | Ensures every `.then()` callback returns a value.              |
| `promise/no-promise-in-callback` | **warn**  | Warns when promises are created inside Node-style callbacks.   |

**Tuning**: Disabled for Cypress test files because Cypress's API uses promise-like chains.

#### 5. `eslint-plugin-n` — Node.js API Misuse Detection

Official replacement for the deprecated `eslint-plugin-node`.

| Rule                  | Severity  | What It Does                                     |
| --------------------- | --------- | ------------------------------------------------ |
| `n/no-deprecated-api` | **error** | Flags use of deprecated or removed Node.js APIs. |

Disabled rules:

- `n/no-missing-require` — disabled because the project uses ESM imports.
- `n/no-unsupported-features/node-builtins` — disabled for `.ts/.tsx` since frontend code runs in browsers.

#### 6. `eslint-plugin-regexp` — Regex Safety

Prevents catastrophic regex backtracking (ReDoS) and invalid patterns.

| Rule                                  | Severity  | What It Does                                                                           |
| ------------------------------------- | --------- | -------------------------------------------------------------------------------------- |
| `regexp/no-super-linear-backtracking` | **error** | Detects regex patterns with nested quantifiers that exhibit catastrophic backtracking. |
| `regexp/no-useless-flag`              | **warn**  | Flags regex flags that have no effect.                                                 |
| `regexp/prefer-character-class`       | **warn**  | Suggests `[abc]` over `a\|b\|c`.                                                       |

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

| Tool               | Scope        | What ESLint Misses                        |
| ------------------ | ------------ | ----------------------------------------- |
| `npm audit`        | Dependencies | Known vulnerabilities in `node_modules`   |
| `trufflehog`       | Git history  | Secrets committed in past commits         |
| CodeQL             | Data flow    | Taint analysis across function boundaries |
| `bandit` (backend) | Python code  | Backend-specific security patterns        |

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

\*\*Never bypass hooks with `--no-verify` or any other mechanism. If a hook fails, resolve the underlying issue instead of bypassing it. The CI build and deployment pipeline will fail (or ship broken code) without these fixes, so bypassing the hook only hides the problem and breaks the pipeline.

## Kilo AI Code Reviews & Security Agent

[Kilo Code](https://kilo.ai) is integrated into this repository via a GitHub App. It provides two automated security and quality services: **AI Code Reviews** on pull requests and a **Security Agent** that triages dependency vulnerabilities.

### AI Code Reviews

Kilo's Code Reviewer automatically analyzes every pull request opened or updated on `DragonStone12/IOPHA`. The agent uses the **Auto Frontier** AI model and is configured in **Strict** review style, which flags all potential issues and prioritizes quality and security.

| Setting           | Value                                                          |
| ----------------- | -------------------------------------------------------------- |
| AI Model          | Auto Frontier                                                  |
| Review Style      | Strict                                                         |
| PR Gate Threshold | Critical issues only                                           |
| Trigger           | PR opened, new commits pushed, PR reopened, draft marked ready |

**PR Gate Threshold** — When set to "Critical issues only", the Kilo review posts a failing status check on the PR if any critical-severity findings are detected. This blocks merging until the critical issues are resolved or the threshold is adjusted.

**Focus Areas** — The reviewer is configured to check all six focus areas:

| Focus Area               | What It Catches                                        |
| ------------------------ | ------------------------------------------------------ |
| Security vulnerabilities | SQL injection, XSS, unsafe APIs, hardcoded secrets     |
| Performance issues       | N+1 queries, inefficient loops, unnecessary re-renders |
| Bug detection            | Logic errors, edge cases, null handling                |
| Code style               | Formatting, naming conventions, consistency            |
| Test coverage            | Missing or inadequate tests for changed code           |
| Documentation            | Missing JSDoc, outdated comments                       |

The reviewer also respects the repository's `REVIEW.md` file, which provides domain-specific review guidance, severity calibration, and sub-agent routing instructions.

### Security Agent

The Kilo Security Agent syncs **GitHub Dependabot alerts** and performs AI-powered triage to determine whether each CVE is actually exploitable in this codebase. It operates in two phases:

1. **AI Triage** — Evaluates package, advisory, severity, and dependency context without opening the repository sandbox. Routes each finding to: _Safe to Dismiss_, _Needs Analysis_, or _Needs Review_.
2. **Sandbox Analysis** — For findings that need deeper investigation, the agent inspects actual repository usage, identifies relevant files and code paths, captures evidence, and recommends a fix.

| Setting               | Value                                                                  |
| --------------------- | ---------------------------------------------------------------------- |
| Auto-analysis         | Enabled — All severities                                               |
| Auto-remediation      | Enabled — All severities (opens PRs for eligible exploitable findings) |
| Finding notifications | Email on — High and above                                              |
| SLA compliance        | 100% (no assigned deadlines)                                           |
| Codebase risk         | 100% (0 open findings)                                                 |

**Analysis Outcomes** — Each security finding is classified into one of:

| Outcome                  | Meaning                                                     |
| ------------------------ | ----------------------------------------------------------- |
| Confirmed exploitable    | The vulnerable code path is reachable in this codebase      |
| Not exploitable          | The vulnerable dependency is not used in an exploitable way |
| Needs your review        | The agent could not determine exploitability automatically  |
| Analysis not complete    | Sandbox analysis has not yet run                            |
| No SLA deadline assigned | Finding is tracked but no remediation deadline is set       |

**Auto-remediation** — When enabled for all severities, Kilo automatically opens a pull request with a suggested fix for every eligible exploitable finding. Duplicate PRs are suppressed. The finding is not closed until Dependabot reports it fixed or a user manually dismisses it.

**SLA Tracking** — Remediation deadlines can be set per severity level. The dashboard tracks whether findings are resolved within their deadlines and sends warning/breach notifications.

### How This Complements Existing Security Layers

| Layer                               | Tool                                  | When It Runs                          |
| ----------------------------------- | ------------------------------------- | ------------------------------------- |
| Local static analysis               | ESLint + security plugins             | Pre-commit (Husky)                    |
| Local dependency audit              | `npm audit`                           | Pre-push (Husky)                      |
| CI static analysis                  | ESLint → SARIF → GitHub Code Scanning | GitHub Actions on push/PR             |
| CI dependency audit                 | `npm audit --audit-level=high`        | GitHub Actions on push/PR             |
| **AI code review**                  | **Kilo Code Reviewer**                | **On PR open/update**                 |
| **Dependency vulnerability triage** | **Kilo Security Agent**               | **Continuous (Dependabot sync)**      |
| **Auto-remediation PRs**            | **Kilo Security Agent**               | **When exploitable finding detected** |

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

### Pull Request Gating Policies

All pull requests to `main` branch must pass the following quality gates:

| Gate               | Tool                  | CI Status                         |
| ------------------ | --------------------- | --------------------------------- |
| Ruff Linting       | `ruff check`          | Required - auto-fix on pre-commit |
| Ruff Formatting    | `ruff format --check` | Required - auto-fix on pre-commit |
| Mypy Type Checking | `mypy`                | Required - strict mode            |
| Bandit Security    | `bandit`              | Warning (medium+ severity)        |
| pip-audit          | `pip-audit`           | Required - high severity block    |
| ESLint             | Frontend lint         | Required                          |

**Pre-Commit Enforcement**: The Husky pre-commit hook (`.husky/pre-commit`) runs `ruff check --fix` + `ruff format` on staged Python files, then a verifying `ruff check` / `ruff format --check` that rejects the commit if any issue remains. The Husky pre-push hook (`.husky/pre-push`) runs `mypy` and `bandit` against the entire `IOPHA-backend/` tree, mirroring CI. Never bypass with `--no-verify`.

### HIPAA Alignment

| Control                          | Implementation                                              |
| -------------------------------- | ----------------------------------------------------------- |
| Access Control (§164.308)        | Role-based auth (patient, admin), JWT with httpOnly cookies |
| Audit Controls (§164.312)        | Server-side logging of PHI access, immutable audit trails   |
| Transmission Security (§164.312) | TLS 1.3 for all external connections                        |
| Storage Encryption               | AES-256 at rest for database and S3                         |
| Integrity Controls               | SARIF + ESLint prevents code-level vulnerabilities          |

### Security Audit

The pre-push hook runs `npm audit --omit=dev --audit-level=high`. Known high-severity dependency vulnerabilities block the push until resolved.

## Testing Security Guardrails

### Test Mock Isolation

- **No live data stubs**: Test mocks must not contain real patient records, user credentials, or production API keys
- **No auth configuration leakage**: Test fixtures must not embed live JWT secrets, OAuth tokens, or database credentials
- **Dependency overrides only**: Use FastAPI `app.dependency_overrides` to inject test doubles; never patch environment variables or global modules

### Data Classification in Tests

| Test Data Type | Allowable | Guardrail |
|---|---|---|
| Synthetic PII | Yes | Generated via factory functions, not copied from production |
| Live PHI | No | Never import production database dumps into test fixtures |
| Real credentials | No | Use dummy values (`test@example.com`, `+1-555-000-0000`) |
| Production URLs | No | Override with `http://test` or mock transports |

### Lifecycle & Cleanup

- Reset `app.dependency_overrides` between tests via fixture teardown
- Transaction-scoped database fixtures roll back all changes per test
- Test artifacts (screenshots, logs) auto-excluded from version control

### Configuration Guide (Models & APIs Not Implemented Yet)

Once models and API endpoints exist, configure `PathSanitizer` and
`PIISanitizationMiddleware` in `app/logging.py` and `app/main.py`
using the pattern definitions below.

**Canonical `PATH_PATTERNS`** — place in `app/logging.py` `PathSanitizer`:

```python
PATH_PATTERNS = [
    (re.compile(r"/patients/\d+"), "/patients/:id"),
    (re.compile(r"/providers/\d+"), "/providers/:id"),
    (re.compile(r"/sessions/\d+"), "/sessions/:id"),
    (re.compile(r"/users/\d+"), "/users/:id"),
]
```

**Canonical `SENSITIVE_QUERY_KEYS`** — place in `app/logging.py` `PathSanitizer`:

```python
SENSITIVE_QUERY_KEYS = {
    "ssn",
    "email",
    "phone",
    "medical_record_number",
    "mrn",
    "dob",
    "date_of_birth",
}
```

**`PIISanitizationMiddleware` sensitive keys** — place in `app/main.py` middleware:

```python
sensitive_keys = {"ssn", "email", "phone", "medical_record_number"}
```

**`PII_PATTERNS` and `redact_pii`** — place in `app/main.py` when PII fields are
confirmed in the domain:

```python
PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[EMAIL_REDACTED]"),
    (re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"), "[PHONE_REDACTED]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN_REDACTED]"),
    (re.compile(r"\b\d{4}[- ]\d{4}[- ]\d{4}[- ]\d{4}\b"), "[CARD_REDACTED]"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[IP_REDACTED]"),
]
```

**How it works together once enabled:**
1. `PathSanitizer.sanitize_path` replaces dynamic ID segments with `:id` placeholders
2. `PathSanitizer.sanitize_query` redacts sensitive query keys with `[REDACTED]`
3. `PIISanitizationMiddleware` applies these rules to every incoming request before logging/metrics
4. `PIISanitizerFilter` applies PII regex redaction to all log records at the root logger level

**Important:** Only configure patterns that match actual implemented models and API responses. Do not add speculative patterns (e.g., `/patients/`, `/providers/`) before the corresponding routes and models exist.

### HTTP Transport Middleware

`PIISanitizationMiddleware` is registered **before** logging and metrics middleware in the FastAPI app initialization. It:

- Normalizes dynamic URL paths using robust regex (e.g., `/patients/12345`, `/patients/123e4567-e89b-12d3-a456-426614174000`, or `/providers/dr-emily-chen` → `/patients/:id`, `/providers/:id`)
- Redacts sensitive query parameters (`ssn`, `email`, `phone`, `medical_record_number`)
- Attaches sanitized values to `request.state` for downstream middleware access

**Path sanitization regex pattern:**

```python
# CORRECT — matches any non-empty path segment (numeric IDs, UUIDs, slugs)
re.sub(r"/patients/[^/]+", "/patients/:id", request.url.path)

# WRONG — \d+ only matches numeric IDs; UUIDs, slugs, and alphanumeric IDs leak into logs
re.sub(r"/patients/\d+", "/patients/:id", request.url.path)
```

**Why `[^/]+` instead of `\d+`:** URL path segments can be numeric IDs, UUIDs (`123e4567-e89b-12d3-a456-426614174000`), slugs (`dr-emily-chen`), or alphanumeric tokens. Using `\d+` silently skips non-numeric identifiers, exposing them in CloudWatch logs and Prometheus metrics. `[^/]+` matches any sequence of non-slash characters, ensuring all ID formats are redacted. Over-sanitizing a known subpath (e.g., `/patients/search` → `/patients/:id`) is acceptable because the priority is preventing PHI leakage, not preserving exact route taxonomy in logs.

### Logging Framework Filter

`PIISanitizerFilter` is a Python standard `logging.Filter` attached to the root logger. It:

- Intercepts all log records before JSON serialization
- Regex patterns redact PII from `record.msg`, `record.args`, and any string values in `record.__dict__`
- Handles `record.args` tuple immutability by reconstructing and reassigning the tuple
- Uses optimized regex to prevent catastrophic backtracking in the async event loop

**Important — Python `logging.extra` semantics:** The `extra` dict passed to `logger.info("msg", extra={...})` is **merged into `record.__dict__`** by the logging framework, not stored as `record.extra`. The filter therefore iterates `record.__dict__` to catch merged `extra` fields. Tests must simulate this behavior by assigning directly to `record.__dict__`, not `record.extra`.

```python
# CORRECT — simulates real Python logging behavior
record.__dict__["email"] = "admin@example.com"
record.__dict__["phone"] = "555-123-4567"

# WRONG — record.extra is never set by the logging framework;
# this tests a code path that does not execute in production.
record.extra = {"email": "admin@example.com", "phone": "555-123-4567"}
```

**Regex Patterns**:

| Pattern                                   | Replacement        | Purpose                 |
| ----------------------------------------- | ------------------ | ----------------------- | --------------- |
| `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z | a-z]{2,}\b`        | `[EMAIL_REDACTED]`      | Email addresses |
| `\b\d{3}[-.]?\d{3}[-.]?\d{4}\b`           | `[PHONE_REDACTED]` | Phone numbers           |
| `\b\d{3}-\d{2}-\d{4}\b`                   | `[SSN_REDACTED]`   | Social security numbers |

Redaction is performed by targeted substring replacement: only the matched PII span is swapped for its `[*_REDACTED]` token while all surrounding, non-sensitive text is preserved. This keeps free-form content (e.g. chat messages) useful for callers and logs instead of being wholly withheld.

### Pydantic DTO Serialization

External-facing Pydantic response models use `@field_serializer` to automatically mask PII fields during serialization. Internal domain models remain unmasked for database operations.

**Separation Rationale**: Applying serializers to internal domain models would mask data needed for database writes and internal business logic. By separating internal models from external DTOs, serializers only apply at the API boundary.

### HIPAA Compliance

| Control                          | Implementation                                                                           |
| -------------------------------- | ---------------------------------------------------------------------------------------- |
| Audit Controls (§164.312)        | PII/PHI sanitization in logging ensures no sensitive data reaches CloudWatch             |
| Transmission Security (§164.312) | Query parameter redaction prevents sensitive data leakage in URLs                        |
| Integrity Controls               | Path normalization prevents metric cardinality attacks and infrastructure fingerprinting |

## Structured JSON Logging Compliance

### PHI Prevention in Logs

All HTTP request/response logs are emitted as structured JSON through `CentralizedLoggingMiddleware`. The following sanitization boundaries prevent PHI leakage:

| Boundary | Implementation | Purpose |
|---|---|---|
| URL path | Regex normalization (`/patients/\d+` → `/patients/:id`) | Prevents cardinality explosion and infrastructure fingerprinting |
| Query parameters | Redaction of `ssn`, `email`, `phone`, `medical_record_number` | Prevents sensitive data exposure in log aggregators |
| User identifiers | Masking (`user_123456` → `user_***456`) | Preserves traceability while limiting PII exposure |
| Response body | Header-only metrics (`content-length`) | Avoids streaming response body extraction which can freeze async middleware |

### Log Aggregation Security

| Control | Implementation |
|---|---|
| Output format | Structured JSON via `JsonTelemetryFormatter` for CloudWatch/Elasticsearch |
| Log destination | stdout only; external log shippers configured at infrastructure level |
| Sensitive data exclusion | No raw database keys, medical histories, or cleartext credentials in `extra_context` |
| Performance | Lightweight regex patterns; no body extraction; no blocking I/O in async middleware |

### Audit Trail Requirements

| Requirement | Implementation |
|---|---|
| Tracking identifier | `X-Request-ID` header propagated through all log entries |
| Runtime duration | `durationMs` field recorded for every transaction |
| Payload size | `responseSize` from `content-length` header |
| Timestamp | ISO 8601 format for cross-system correlation |
| Immutable logs | Logs streamed to stdout; tamper-proof once ingested by external shipper |

### Error Response Payload Hygiene

The global exception handlers (`app/utils/handlers.py`) return structured JSON
problem payloads to clients. These payloads are explicitly scrubbed so no
operational or sensitive data leaves the trust boundary:

| Boundary | Rule | Enforcement |
|---|---|---|
| Raw trace data | Exception text, `repr()`, memory addresses, and `exc_info` are **never** placed in `detail` or any response field | Global `Exception` handler emits a fixed generic `detail`; raw trace is captured server-side only via `logger.error(..., exc_info=True)` |
| Credentials & secrets | No JWTs, API keys, OAuth tokens, or database DSNs in any payload attribute | Only opaque identifiers (slot/session/patient ids) are referenced, and only in `detail`/`log_context` |
| Database schemas | No table names, column names, SQL, or query plans in client payloads | Handlers build `detail` from fixed templates + non-sensitive identifiers only |
| Log vs payload separation | Sensitive context lives only in `extra_context` server logs; client sees only `help_url` | `extra_context` flows through `JsonTelemetryFormatter`; response body omits `extra_context` entirely |

`detail` is human-readable and client-safe; it must not contain interpolation
of `str(exc)` or any untrusted exception attribute.

### Structured JSON Logging: PHI & Structural-Identifier Scrubbing

The provider/physician scheduling pipeline confirms that every property
emitted by the structured JSON formatting engine is cleared of confidential
PHI parameters and private session details before streaming to stdout:

| Boundary | Rule | Enforcement |
|---|---|---|
| Structural identifiers | The internal `ProviderRecord.db_primary_key` persistence key is dropped by `map_provider_to_physician()` and never reaches `PhysicianSchema` or the response body | `app/schemas/provider/mappers.py` |
| Credentials & secrets | `JsonTelemetryFormatter` emits only curated fields (`timestamp`, `level`, `logger`, `message`, `requestId`) plus an explicit `extra_context` dict; raw `record` internals, credentials, and query values are never serialized | `app/utils/logging.py` |
| Correlation id exposure | `X-Request-ID` is client-supplied and propagated as-is; it is never masked, preserving distributed traceability | `app/utils/context.py`, `app/middleware/request_tracing.py` |
| Context isolation | `request_id_ctx` (a `contextvars.ContextVar`) is reset in a `finally` block after every request, preventing trace state from leaking across requests or background tasks | `app/middleware/request_tracing.py` |
| HTTP exception detail | Starlette `HTTPException.detail` is never serialized into the client response; the global handler emits a static safe string to avoid leaking internal exception structures | `app/utils/handlers.py` |

All scheduling responses and error payloads are validated by tests that assert
no structural identifier (`db_primary_key`) and no leak markers
(`Traceback`, `0x`, `password`, `secret`, `Bearer `, `postgresql`) appear in the
client response.

**Related Documentation:**

- [ESLint Security & Bug Detection](ESLINT_SECURITY_BUG_DETECTION.md)
- [Ruff & Mypy Linting Rules](RUFF_MYPY_LINTING.md)
- [SARIF](security/SARIF.md)
- [Architecture](../infra/ARCHITECTURE.md)
- [Cypress Testing Guide](../testing/CYPRESS_TESTING.md)
- [Kilo Code Reviews Documentation](https://kilo.ai/docs/automate/code-reviews/overview)
- [Kilo Security Agent Documentation](https://kilo.ai/docs/deploy-secure/security-reviews)

## Time Slot Availability API Security

### PHI Scrubbing Patterns & Regex Rules

The availability pipeline scrubs the following PHI/PII patterns from every log
record before serialization (`app/core/phi_scrubber.py`):

| Pattern | Regex | Replacement | Purpose |
|---|---|---|---|
| Email | `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b` | `[REDACTED]` | Contact emails in user-facing errors |
| SSN | `\b\d{3}-\d{2}-\d{4}\b` | `[REDACTED]` | Social security numbers |
| Phone | `(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b` | `[REDACTED]` | North American phone numbers |
| DOB | `\b(0[1-9]|1[0-2])[/-](0[1-9]|[12]\d|3[01])[/-]\d{4}\b` | `[REDACTED]` | Dates of birth (MM/DD/YYYY only) |
| Labeled name | `\b(?:name|patient|member|contact|dob)\s*[:=]\s*(?:[^\W\d_]+(?:[-'][^\W\d_]+)*\s+){1,}[^\W\d_]+(?:[-'][^\W\d_]+)*` | `[REDACTED]` | PHI introduced with recognizable labels |

**Explicit non-pattern:** ISO calendar dates (`YYYY-MM-DD`) are **not**
redacted because `TimeSlotSchema.id` embeds real ISO dates (e.g.
`2024-01-15-09:00 AM`). Redacting those would corrupt legitimate availability
logs and break log correlation.

**Scrubber semantics:** `PHIScrubber` is side-effect free. It returns a copy
with matches replaced; the original is never mutated.

### HIPAA Logging Compliance

All availability API request/response logs are emitted as structured JSON
through `JsonTelemetryFormatter` / `JSONLogFormatter`.

| Boundary | Implementation | Purpose |
|---|---|---|
| URL path | Raw path passed through to structured logs | `/api/providers/{provider_id}/slots` does not embed PHI; cardinality is protected by Prometheus path grouping. |
| Query parameters | Sanitized by `CentralizedLoggingMiddleware` before logging | No sensitive query keys are expected on availability routes, but the middleware passes them through the JSON formatter where PHI patterns are scrubbed. |
| Slot identifiers | `TimeSlotSchema.id` embeds an ISO date; dates are not redacted by PHIScrubber | Calendar dates are not PHI under HIPAA; they are required for log correlation and debugging. |
| Provider names | Never logged; only `providerId` (opaque directory key) is emitted | `ProviderNotFoundException` logs `providerId`, not provider name. |
| Response body | Only status code and content-length are logged | `CentralizedLoggingMiddleware` avoids body extraction to prevent async freezes. |

### Request ID Tracing for Audit Purposes

`X-Request-ID` is the canonical correlation identifier for every availability
transaction:

- **Generation:** `RequestTrackingMiddleware` mints a UUID if the client does not
  supply one.
- **Validation:** Only syntactically valid UUIDs are trusted from the client to
  prevent trace spoofing.
- **Propagation:** Bound to `request_id_ctx` `ContextVar` at the start of the
  request; accessible to logging, services, repositories, and background tasks
  without explicit parameter threading.
- **Echo:** Returned on the response `X-Request-ID` header for client-side
  correlation.
- **Reset:** The context var token is reset in a `finally` block after every
  request so trace state cannot leak across requests or async tasks.
- **Log inclusion:** Every structured JSON log line carries `requestId` sourced
  live from `request_id_ctx` by `JsonTelemetryFormatter`.

**Audit trail fields** present in every availability transaction log:

| Field | Description |
|---|---|
| `timestamp` | ISO 8601 event time |
| `level` | Log severity |
| `requestId` | Correlation UUID |
| `method` | HTTP method |
| `path` | Request path |
| `message` | `request.start` or `request.complete` |
| `status` | HTTP response status |
| `durationMs` | Request processing duration |
| `slotId` | Present only on `timeslot.unavailable` events |
| `providerId` | Present only on `directory.provider_not_found` events |

### Input Sanitization & Validation Rules

All availability inputs are validated before business logic executes:

- `TimeSlotSchema` enforces `extra="forbid"` so no unplanned fields can cross
  the API boundary.
- `id` and `time` fields are validated against strict Pydantic regex patterns
  (`SLOT_ID_PATTERN` and `TIME_PATTERN`) so malformed slots are rejected at
  the schema layer.
- `InvalidTimeSlotFormatException` is raised for any slot id that does not
  match the expected `YYYY-MM-DD-h:MM AM/PM` format, returning HTTP 400 with
  a scrubbed detail string.
- `ProviderNotFoundException` is raised when the provider id resolves to no
  directory record, returning HTTP 404.
- `TimeSlotUnavailableException` is raised when a reservation is attempted on
  a non-existent or already-reserved slot, returning HTTP 409.

**Validation coverage:**
- Schema instantiation and service-layer validation are covered by unit tests.
- RFC-7807 error payloads are validated with `LEAK_MARKERS` assertions ensuring
  no stack traces, memory addresses, or credentials appear in client responses.

### OpenAPI Error Contract

`app/main.py` rewrites every 422 response to reference `ProblemDetail` and
registers the `ProblemDetail` schema in `components/schemas`. The published
contract matches the real error object returned to clients, including the
`help_url` runbook link.

**Related Documentation:**

- [Technical Design](../infra/TECHNICAL_DESIGN.md)
- [Structured JSON Logging Compliance](#structured-json-logging-compliance)
- [Sensitive Data Handling](SENSITIVE_DATA_HANDLING.md)
- [Input Validation](INPUT_VALIDATION.md)
- [Runbooks](RUNBOOKS.md)
