# IOPHA — Interactive Obesity Prevention Health Assistant

IOPHA is an AI-powered health assistant that delivers personalized, evidence-based obesity prevention guidance and routes high-risk users to in-network medical professionals immediately after risk detection. The system operates within hospital and healthcare organization ecosystems, delivering dual-pathway interventions: self-directed prevention tips and direct care scheduling.

## Documentation

| Document | Description |
|---|---|
| [Architecture](docs/ARCHITECTURE.md) | High-level system design: architecture diagram, trust boundaries, AWS infrastructure topology, data flow sequences (chat and document ingestion), HIPAA compliance alignment, and third-party integrations (pgvector, Textract, LLM). |
| [Technical Design](docs/TECHNICAL_DESIGN.md) | Low-level design: technology stack, monorepo structure, frontend implementation (styling, logging, state management, performance monitoring), backend API spec, database schema, RAG pipeline logic, testing strategy, and CI/CD workflows. |
| [Cypress Testing Guide](docs/CYPRESS_TESTING.md) | Complete Cypress 15 testing reference: E2E BDD with Cucumber, component testing with `cy.mount()`, step definition organization rules, mandatory TDD workflow, scoped selectors, and troubleshooting common errors. |
| [Visual Regression Playbook](docs/VISUAL_REGRESSION_PLAYBOOK.md) | Best practices for visual regression testing with `cypress-image-diff-js`: browser launch flags, dynamic content normalization, snapshot naming conventions, baseline management, overflow handling, responsive design testing, and flaky test stabilization. |
| [ESLint Security & Bug Detection](docs/ESLINT_SECURITY_BUG_DETECTION.md) | Security and bug detection via ESLint plugins: code injection, XSS prevention, hardcoded credential scanning, cognitive complexity, promise handling, Node.js API misuse, regex safety (ReDoS), CI SARIF integration, and violation handling. |
| [Security Overview](docs/SECURITY.md) | Unified security documentation: trust boundaries, PHI handling, static analysis, dependency auditing, PII handling in frontend flows, HIPAA compliance, and quick reference commands. |
| [Troubleshooting](TROUBLESHOOTING.md) | Known issues and solutions: Vite environment variable pitfalls, IOPHA Resources integration, Tailwind CSS v4 configuration, Cypress overflow clipping, duplicate text labels, React import errors, and logging/performance hooks. |
| [Appointment Flow](docs/features/APPOINTMENT_FLOW.md) | Physician appointment booking flow implementation details |
| [SARIF Justification](docs/security/SARIF_JUSTIFICATION.md) | SARIF security report format rationale and integration notes |
| [Business Case](docs/product_plan/BUSINESS_CASE.md) | Product business case and market analysis |
| [Product Requirements](docs/product_plan/PRD.md) | Product requirements document with feature specifications |

## Running the code

### Frontend

```bash
cd IOPHA-frontend && npm install && npm run dev
```

### Backend

```bash
cd IOPHA-backend && pip install -r requirements.txt && uvicorn app.main:app --reload
```

## Quick Start

| Command | Description |
|---|---|
| `npm run dev` | Start Vite development server |
| `npm run build` | Production build |
| `npm run lint` | Run ESLint with security and bug checks |
| `npm run test:e2e` | Run Cypress E2E tests (Cucumber BDD) |
| `npm run cy:check-steps` | Check for duplicate step definitions |
| `npm audit` | Check dependency vulnerabilities |
  