# IOPHA: Technical Design (Low-Level Design)

## Table of Contents

| # | Section | Description |
|---|---------|-------------|
| 1 | [Technology Stack](#1-technology-stack) | Frontend, backend, database, and testing technologies |
| 2 | [Project Structure](#2-project-structure-monorepo) | Monorepo directory layout |
| 3 | [Frontend Implementation](#3-frontend-implementation-details) | Styling, logging, state management, performance |
| 4 | [Backend Implementation](#4-backend-implementation-details) | API spec, database schema, RAG pipeline |
| 5 | [Testing Strategy](#5-testing-strategy) | Unit, integration, E2E, visual regression, performance |
| 6 | [CI/CD & Deployment](#6-cicd--deployment) | GitHub Actions, environment config, local dev |
| 7 | [Decision Points](#7-decision-points-pending) | Pending architectural decisions |

## 1. Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Frontend Framework | React | 18 |
| Language | TypeScript | 5 |
| Build Tool | Vite | 8 |
| Styling | Tailwind CSS | v4 |
| Component Library | shadcn/ui + Radix UI | Confirmed |
| Backend Framework | FastAPI | Latest |
| Language | Python | 3.11+ |
| ORM | SQLAlchemy | Latest |
| Validation | Pydantic | Latest |
| Database | PostgreSQL | 15 |
| Vector Extension | pgvector | Latest |
| Testing (Backend) | pytest | Latest |
| Testing (E2E) | Cypress | Latest |
| Load Testing | Locust | Latest |

## 2. Project Structure (Monorepo)

```
/IOPHA
├── /IOPHA-frontend
│   ├── /src
│   │   ├── /components        # React components (each in own directory)
│   │   │   ├── /LandingPage/
│   │   │   ├── /RiskProfileSidebar/
│   │   │   ├── /ChatArea/
│   │   │   └── /ui/           # shadcn/ui primitives (copied from IOPHA Resources)
│   │   ├── /hooks           # Custom hooks (useLogRenders, usePerformanceTracking)
│   │   ├── /utils
│   │   │   ├── logger.ts      # Custom Logger class
│   │   │   └── performance.js # Performance monitoring utilities
│   │   ├── /services          # API client wrappers
│   │   ├── /types             # TypeScript interfaces
│   │   └── App.tsx
│   ├── cypress.config.ts
│   └── package.json
├── /IOPHA-backend
│   ├── /app
│   │   ├── /api               # Route definitions
│   │   ├── /services          # Business logic (RAG, directory, ingestion)
│   │   ├── /core
│   │   │   ├── auth.py        # JWT middleware, dependencies
│   │   │   ├── config.py      # Settings management
│   │   │   └── database.py    # SQLAlchemy setup
│   │   └── main.py
│   ├── /tests                 # pytest tests
│   └── pyproject.toml
├── /infra                     # Terraform/CDK configurations
```

## 3. Frontend Implementation Details

### 3.1 Styling with Tailwind CSS

The frontend uses Tailwind CSS v4 with the IOPHA brand theme (copied from IOPHA Resources):
- Primary color: `#0A6B7C` (teal)
- Accent color: `#D95B3B` (orange)
- Background: `#F3F1EC` (warm off-white)
- All component styling uses Tailwind utility classes via the `cn()` helper (clsx + tailwind-merge)

UI components are sourced from IOPHA Resources (shadcn/ui primitives) and copied into `src/components/ui/`. Components use Radix UI primitives under the hood (`@radix-ui/react-*` packages).

### 3.2 Logging & Observability

**Custom Logger Class** (`src/utils/logger.ts`):
```typescript
class Logger {
  static debug(message: string, ...args: unknown[]): void
  static info(message: string, ...args: unknown[]): void
  static warn(message: string, ...args: unknown[]): void
  static error(message: string, ...args: unknown[]): void
}
```

Environment behavior:
- Development: Logs all levels (debug, info, warn, error)
- Production: Suppresses debug, info, warn; only error level emitted

**Namespace Helpers**:
- `app:render`, `app:api`, `app:router` - selective console output for application domains
- No-ops in production builds

**Render-Tracking Hook** (`useLogRenders`):
- Monitors functional component render frequency using `useRef` and `useEffect`
- Logs render count and optional shallow prop snapshot
- Available in `src/hooks/useLogRenders.ts`

**Error Boundaries** (`src/components/AppErrorBoundary.tsx`):
- Uses `react-error-boundary` for functional error boundaries
- Russian Doll pattern: Root → Layout → Feature level isolation
- Structured error logging: message, stack, component stack
- Fallback UI: Localized with "Try again" reset button, no external API calls

### 3.3 State Management & Data Fetching

Strategy:
- Server state: React Query (TanStack Query) or SWR for caching, background updates
- Client state: React Context or Zustand for UI state

### 3.3 Performance Monitoring

**React Profiler Integration**:
- Root-level and route-boundary profiling
- `onRender` callback logs: id, phase, actualDuration, baseDuration, startTime, commitTime

**Performance Hook** (`usePerformanceTracking`):
- Captures render durations via `useRef` and `useLayoutEffect`/`useEffect`
- Warning emitted if render exceeds 16ms (60fps threshold)

**Page Metrics** (`logPagePerformanceMetrics`):
- DNS lookup, TCP connection, TTFB, DOM interactive, DOM loaded, load complete
- First Paint, First Contentful Paint via Paint Timing API

## 4. Backend Implementation Details

### 4.1 API Specification

**Authentication**:
- JWT Access tokens (15 min expiration)
- Refresh tokens (7 days expiration)
- Stored in httpOnly cookies

**Endpoints**:

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | /auth/register | User registration | No |
| POST | /auth/login | Login with email/password | No |
| POST | /auth/refresh | Refresh access token | No |
| GET | /chat | WebSocket for streaming chat | Yes |
| POST | /chat/message | Send message endpoint | Yes |
| GET | /directory | Physician lookup | Yes |
| POST | /ingest | Trigger manual document ingestion | Admin only |

**Error Handling**:
- Consistent JSON error format: `{ code, message, details }`
- RFC 7807 Problem Details for HTTP APIs

### 4.2 Database Schema

**Tables**:

| Table | Purpose |
|-------|---------|
| users | User accounts with role (patient/admin) |
| organizations | Hospital/health system affiliations |
| sessions | Chat session tracking |
| messages | Chat message history |
| guidelines | Clinical guidelines with vector column |
| ingestion_jobs | Document processing status |

**Indexes**:
- GIN indexes for full-text search on text columns
- IVFFlat index for vector similarity search on embeddings

**pgvector Configuration**:
- `PGVECTOR_DIMENSION` default: 1536 (text-embedding-3-small)
- HNSW or IVFFlat index strategy based on dataset size

### 4.3 RAG Pipeline Logic

**Chunking Strategy**:
- 512-token windows with 10% overlap (51 tokens)
- Text splitter preserves sentence boundaries

**Embedding Model**:
- `text-embedding-3-small` (OpenAI) or equivalent

**Retrieval Flow**:
1. User query encoded to vector
2. Similarity search against guidelines table
3. Top-K results retrieved
4. Fallback to full-text search if vector search fails

## 5. Testing Strategy

### 5.1 Unit Tests
- Framework: pytest
- Coverage target: 80%
- Location: `/IOPHA-backend/tests/`

### 5.2 Integration Tests
- FastAPI TestClient for all API routes
- Database transactions rolled back per test
- MinIO for local S3-compatible storage

### 5.3 E2E Tests
- Framework: Cypress with Cucumber Preprocessor
- Browsers: Chrome, Firefox, Edge (matrix strategy)
- `fail-fast: false` for full browser coverage

### 5.4 Visual Regression Tests
- Tool: cypress-image-diff-js
- Artifacts: `cypress-visual-screenshots/`, `cypress-visual-report/`
- Auto-excluded via `.gitignore`

### 5.5 Performance Tests
- Tool: Locust
- Target: 100 concurrent users, <2s p95 latency

### 5.6 Code Quality & Linting

**For more information, read the security document.** ([docs/SECURITY.md](SECURITY.md))

**ESLint Configuration**:
- Version: ESLint 9.x (flat config format)
- Config file: `eslint.config.js` (replaces deprecated `.eslintrc.cjs`)
- TypeScript support: `@typescript-eslint/parser` and `@typescript-eslint/eslint-plugin`
- TanStack Query plugin: `@tanstack/eslint-plugin-query` for exhaustive-deps rule
- Ignores: `node_modules/`, `dist/`, `cypress/`

**Lint Script**:
```bash
npm run lint
# Executes: eslint src --max-warnings=0
```

**Pre-commit Hooks**:
- Husky pre-commit hook runs ESLint with `--fix` on staged `.ts` and `.tsx` files
- Pre-push hook runs: lint, duplicate step check, E2E tests, component tests, and security audit

**IMPORTANT: Never bypass hooks with `--no-verify` or any other mechanism. All hooks must run to catch errors locally before they reach CI. The pre-push hook runs the same checks as GitHub Actions (lint, E2E tests, component tests, security audit). If a hook fails, fix the underlying issue instead of attempting to bypass it.

### 5.7 CI Integration
- Tests run on every PR to main
- Screenshots uploaded as artifacts on failure

## 6. CI/CD & Deployment

### 6.1 GitHub Actions Workflows

**ci-frontend.yml**:
- Lint step: `npm run lint` (ESLint 9.x with flat config `eslint.config.js`)
- Duplicate step check: `npm run cy:check-steps`
- E2E tests: `npm run test:e2e` (Cypress with Cucumber BDD)
- Component tests: `npx cypress run --component`
- Security audit: `npm audit --omit=dev --audit-level=high`
- Cypress E2E matrix (chrome, firefox, edge)
- Screenshot artifacts on failure

**Note**: ESLint 9.x uses flat config format (`eslint.config.js`). The deprecated `.eslintrc.cjs` and `.eslintignore` files have been removed. The lint script no longer uses the `--ext` flag (removed in ESLint 9.x).

**ci-backend.yml**:
- Bandit SAST scanning
- pip-audit for dependencies
- pytest unit tests

### 4.4 Observability & Metrics

**Prometheus Instrumentation**:
- Library: `prometheus-fastapi-instrumentator`
- Endpoint: `/metrics`
- Configuration choices:
  - `handle_unhandled_paths=False` — prevents cardinality explosion from undefined routes
  - `should_group_status_codes=True` — groups similar status codes to reduce metric cardinality
  - `should_ignore_untemplated=True` — ignores metrics for requests that don't match any route
  - `excluded_handlers=["/metrics"]` — excludes the metrics endpoint from being instrumented to avoid self-reporting
  - `should_gzip=True` — gzips the payload to reduce network overhead during scraping

**Path Grouping Strategy**:
Dynamic paths like `/api/providers/{provider_id}/slots` are automatically grouped by FastAPI's routing definitions. The instrumentator normalizes these paths before they reach the metrics exporter, preventing high-cardinality metric series.

**Endpoint Security**:
The `/metrics` endpoint is strictly internal. It is blocked at the API Gateway / load balancer level from external/public access and accessible only by the internal Prometheus scraper.

#### Prometheus Metrics Endpoint Security

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

### 6.2 Environment Configuration

**Variables**:

| Category | Variable | Secret |
|----------|----------|--------|
| Auth | JWT_SECRET | Yes |
| Auth | AUTH_PROVIDER_URL | No |
| Database | DATABASE_URL | Yes |
| Vector DB | PGVECTOR_DIMENSION | No |
| AWS | AWS_ACCESS_KEY_ID | Yes |
| AWS | AWS_SECRET_ACCESS_KEY | Yes |
| AWS | AWS_REGION | No |
| AWS | S3_BUCKET_GUIDELINES | No |
| LLM | LLM_API_KEY | Yes |
| LLM | LLM_MODEL | No |
| Email | EMAIL_API_KEY | Yes |
| App | APP_ENV | No |
| App | CORS_ORIGINS | No |

### 6.3 Local Development

```bash
# Frontend development
cd IOPHA-frontend && npm install && npm run dev

# Backend development (requires main.py in app/)
cd IOPHA-backend && pip install -r requirements.txt && uvicorn app.main:app --reload
```

## 7. Decision Points (Pending)

| Component | Options | Criteria |
|-----------|---------|----------|
| Auth Provider | Supabase Auth, Custom JWT | HIPAA compliance, ease of integration |
| Frontend Host | Vercel, Netlify, Cloudflare Pages | Cold start, edge caching |
| Backend Host | Railway, Fly.io, AWS Fargate | Cost, scaling, HIPAA eligibility |
| Database | Neon, Supabase, AWS RDS | HIPAA eligibility, pgvector support |