# IOPHA — Interactive Obesity Prevention Health Assistant

IOPHA is an AI-powered health assistant that delivers personalized, evidence-based obesity prevention guidance and routes high-risk users to in-network medical professionals immediately after risk detection. The system operates within hospital and healthcare organization ecosystems, delivering dual-pathway interventions: self-directed prevention tips and direct care scheduling.

## Documentation

| Document                                                                          | Description                                                                                                                                                                                                                                                   |
| --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Architecture](docs/infra/ARCHITECTURE.md)                                        | High-level system design: architecture diagram, trust boundaries, AWS infrastructure topology, data flow sequences (chat and document ingestion), HIPAA compliance alignment, and third-party integrations (pgvector, Textract, LLM).                         |
| [Technical Design](docs/infra/TECHNICAL_DESIGN.md)                                | Low-level design: technology stack, monorepo structure, frontend implementation (styling, logging, state management, performance monitoring), backend API spec, database schema, RAG pipeline logic, testing strategy, and CI/CD workflows.                   |
| [AWS Technologies](docs/infra/AWS_TECHNOLOGIES.md)                                | Inventory of the deployed AWS stack: Lambda (container-image compute), ECR (image registry), IAM (deploy credentials), Amplify (frontend hosting), API Gateway (public endpoint), manual and CI deployment flows, and planned services.                        |
| [Cypress Testing Guide](docs/testing/CYPRESS_TESTING.md)                          | Complete Cypress 15 testing reference: E2E BDD with Cucumber, component testing with `cy.mount()`, step definition organization rules, mandatory TDD workflow, scoped selectors, and troubleshooting common errors.                                           |
| [Visual Regression Playbook](docs/testing/VISUAL_REGRESSION_PLAYBOOK.md)          | Best practices for visual regression testing with `cypress-image-diff-js`: browser launch flags, dynamic content normalization, snapshot naming conventions, baseline management, overflow handling, responsive design testing, and flaky test stabilization. |
| [ESLint Security & Bug Detection](docs/security/ESLINT_SECURITY_BUG_DETECTION.md) | Security and bug detection via ESLint plugins: code injection, XSS prevention, hardcoded credential scanning, cognitive complexity, promise handling, Node.js API misuse, regex safety (ReDoS), CI SARIF integration, and violation handling.                 |
| [Ruff & Mypy Linting](docs/security/RUFF_MYPY_LINTING.md)                         | Python static analysis rules: Pyflakes, Pycodestyle, isort, Pydocstyle, Bandit Security, Bugbear, and Pylint Refactoring rules with violation handling.                                                                                                       |
| [Security Overview](docs/security/SECURITY.md)                                    | Unified security documentation: trust boundaries, PHI handling, static analysis, dependency auditing, PII handling in frontend flows, HIPAA compliance, and quick reference commands.                                                                         |
| [Sensitive Data Handling](docs/security/SENSITIVE_DATA_HANDLING.md)                | PHI/PII redaction architecture, credential scrubbing, and the PHIScrubber idempotency fix.                                                                                                       |
| [Input Validation](docs/security/INPUT_VALIDATION.md)                              | API schema payload limits, max_length constraints, and DoS prevention for unbounded string fields.                                                                                              |
| [Troubleshooting](TROUBLESHOOTING.md)                                             | Known issues and solutions: Vite environment variable pitfalls, IOPHA Resources integration, Tailwind CSS v4 configuration, Cypress overflow clipping, duplicate text labels, React import errors, and logging/performance hooks.                             |
| [Runbooks](docs/RUNBOOKS.md)                                                      | Backend error mitigation guide: centralized runbook for every structured error response, deep-linked via `help_url` — booking conflicts, time zone mismatch, payload limits, gateway timeouts, notification inconsistencies, and intake/nutrition failures.  |
| [Appointment Flow](docs/features/APPOINTMENT_FLOW.md)                             | Physician appointment booking flow implementation details                                                                                                                                                                                                     |
| [SARIF](docs/security/SARIF.md)                                     | SARIF security report format rationale and integration notes                                                                                                                                                                                                  |                                                                                                                                                                                                  |
| [Business Case](docs/product_plan/BUSINESS_CASE.md)                               | Product business case and market analysis                                                                                                                                                                                                                     |
| [Product Requirements](docs/product_plan/PRD.md)                                  | Product requirements document with feature specifications                                                                                                                                                                                                     |

## Running the code

### Frontend

```bash
cd IOPHA-frontend && npm install && npm run dev
```

### Backend

The backend requires Python 3.11+ and its dependencies installed into a
dedicated virtual environment. **Use the project's own `IOPHA-backend/venv`** —
do not run `uvicorn` from an unrelated environment (for example a different
project's virtualenv). If you do, imports such as
`prometheus_fastapi_instrumentator` fail with
`ModuleNotFoundError: No module named 'prometheus_fastapi_instrumentator'`,
because that environment never had `IOPHA-backend/requirements.txt` installed
into it.

If the virtual environment does not exist yet, create it first:

```bash
cd IOPHA-backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

If the virtual environment already exists (for example `IOPHA-backend/venv`),
just activate it and make sure the dependencies are installed:

```bash
cd IOPHA-backend
source venv/bin/activate
pip install -r requirements.txt
```

Then start the development server from inside the activated environment:

```bash
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000` and auto-reloads on file
changes. Run `deactivate` to leave the virtual environment when finished.

FastAPI also serves its generated OpenAPI schema and interactive documentation
automatically. Once the server is running you can open:

- `http://127.0.0.1:8000/docs` — Swagger UI, the interactive API explorer where
  you can inspect every route and send test requests directly from the browser.
- `http://127.0.0.1:8000/redoc` — ReDoc, an alternative rendered view of the
  same API documentation.
- `http://127.0.0.1:8000/openapi.json` — the raw OpenAPI/JSON schema that
  drives both doc views and any external tooling (e.g. client generators).

Prometheus metrics are exposed at `http://127.0.0.1:8000/metrics`.

### Local quality gates (Git hooks)

This repo uses [Husky](https://typicode.github.io/husky/) for Git hooks (configured via `core.hooksPath = .husky`). After cloning, run `npm install` once so the `prepare` script installs the hooks.

- **Backend**: the pre-commit hook runs `ruff` (auto-fix + verify) on staged Python files in `IOPHA-backend/`. `ruff` must be available on your `PATH` (e.g. `pip install ruff`, or it is resolved from a `venv`/via `python3 -m ruff`). If it is missing the hook fails loudly rather than committing broken code.
- **Frontend**: the pre-commit hook runs `npx lint-staged`.

Never bypass hooks with `--no-verify`.

## Quick Start

| Command                  | Description                             |
| ------------------------ | --------------------------------------- |
| `npm run dev`            | Start Vite development server           |
| `uvicorn app.main:app --reload` | Start FastAPI backend with auto-reload |
| `http://127.0.0.1:8000/docs` | Interactive Swagger UI for the backend API |
| `npm run build`          | Production build                        |
| `npm run lint`           | Run ESLint with security and bug checks |
| `npm run test:e2e`       | Run Cypress E2E tests (Cucumber BDD)    |
| `npm run cy:check-steps` | Check for duplicate step definitions    |
| `npm audit`              | Check dependency vulnerabilities        |
