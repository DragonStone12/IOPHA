# IOPHA: Technical Design Document

## 01 Product Overview

### Purpose
IOPHA bridges the gap between predictive obesity risk detection and actionable prevention by providing an interactive health assistant immediately after a user completes a health risk assessment. It delivers evidence-based, personalized prevention guidance and seamlessly schedules in-network clinical appointments. Clinical guidelines are ingested from scanned documents via an automated OCR and vector-embedding pipeline.

### Target Audience
- **At-risk adults**: Users identified by hospital risk models who need immediate, accessible guidance.
- **Medical administrators**: Stakeholders who need engagement analytics and conversion tracking.
- **In-network physicians**: Providers who receive pre-qualified patient referrals with risk context.

### Expected Outcomes
- 30%+ of at-risk users schedule an in-network visit through the assistant.
- <2 second API response time for chat endpoints.
- 99% uptime during business hours.
- HIPAA-aligned data handling and audit trails.
- Automated ingestion of clinical guidelines from PDF/scanned documents within 24 hours of upload.

## 02 Architecture

### High-Level Architecture
The system is split into two independently deployable services communicating over REST and WebSocket:

- **Frontend (IOPHA-frontend)**: React 18 + TypeScript + Vite 5 SPA. Consumes backend REST endpoints and WebSocket streams for real-time chat.
- **Backend (IOPHA-backend)**: FastAPI application handling auth, chat orchestration, directory queries, appointment scheduling, and pipeline orchestration.
- **PostgreSQL + pgvector**: Primary relational store for users, organizations, physicians, facilities, sessions, messages, and vector embeddings for clinical guidelines.
- **LLM Provider**: Synthesizes retrieved context into natural language responses.
- **Document Ingestion Pipeline**: Scheduled or event-driven process that extracts text from clinical PDFs via AWS Textract, generates vector embeddings, and upserts into pgvector.

### System Interfaces
- **API endpoints**: FastAPI REST routes + WebSocket streaming for real-time chat.
- **Third-party integrations**: LLM API (HTTP), PostgreSQL + pgvector (psycopg/asyncpg), AWS Textract (boto3), S3 (boto3), Hospital directory DB (SQL).
- **Internal modules**: `app/api` (routes), `app/services` (RAG orchestration, directory matching, ingestion pipeline), `app/core` (auth, config, database), `app/workers` (cron / ingestion jobs).

### Document Ingestion Flow
1. Admin uploads clinical guideline PDF to S3 bucket.
2. S3 event notification or cron triggers ingestion job.
3. Backend creates an ingestion job record with status `pending`.
4. AWS Textract processes the document; raw text extracted.
5. Text is chunked (e.g., 512-token windows with overlap).
6. Each chunk is embedded via OpenAI `text-embedding-3-small`.
7. Embeddings are upserted into the guidelines table via the vector extension, with organization and metadata attached.
8. Job marked `completed`; guideline becomes available for RAG retrieval.
9. On failure, error logged in the ingestion job; retry scheduled.

### User Interface
- Dual-action chat interface: immediate tips and nearby physician suggestions side-by-side.
- Accessible, high-contrast design for older and visually-impaired users.
- Responsive layout for desktop and mobile.

### Frontend Logging & Observability
- **Structured logging**: winston is used for browser-safe structured logging. A centralized logger utility (`src/utils/logger.js`) exports `debug`, `info`, `warn`, and `error` methods. JSON formatting is applied in production; colorized console output is used in development.
- **Namespace debugging**: The `debug` package enables granular, namespace-scoped logging (`app:render`, `app:api`, `app:router`). Namespaces are toggled at runtime via the `DEBUG` environment variable or `localStorage.debug`. Debug statements are stripped from production builds to prevent bundle bloat and information leakage.
- **Transport constraints**: Only the Console transport is configured for the browser. Node-specific transports (File, HTTP) are explicitly excluded to avoid bundling Node core modules.
- **APM integration**: Log output is formatted for ingestion by the centralized monitoring stack (Prometheus + Grafana with AWS CloudWatch Logs).

## 03 Data Model

The system uses a relational database with vector-search capabilities for embeddings, plus object storage for raw documents. Core entities cover users, organizations, risk profiles, clinical guidelines, physicians, facilities, chat sessions, messages, and ingestion jobs. The ingestion pipeline runs as scheduled or event-driven tasks, with status tracked in a dedicated jobs table.

## 04 Testing Plan

### Testing Strategy
- **Unit tests**: Service-layer functions (RAG retrieval, directory matching, auth, ingestion pipeline). Coverage target: 80%.
- **Integration tests**: FastAPI TestClient covering all API routes; database transactions rolled back per test; ingestion pipeline mocked against local S3 emulator (MinIO).
- **E2E tests**: Playwright or Cypress covering user registration, consent flow, chat → tips flow, chat → scheduling flow.
- **Performance tests**: Locust or k6 for chat endpoint load testing (target: 100 concurrent users, <2s p95 latency); pgvector similarity query latency benchmark (<500ms p95).

### Testing Tools
- **Frameworks**: pytest (Python), Vitest / React Testing Library (frontend), Playwright (E2E).
- **CI integration**: Tests run in GitHub Actions on every PR to `main`.
- **Code coverage**: Coverage.py with enforcement thresholds in CI.

### Key Test Cases
- Happy path: user registers, consents, sends message, receives tips + physician options.
- Auth: invalid tokens return 401; unauthorized queries return 403.
- RAG: high-risk user receives guideline-based response; no generic content when pgvector is available.
- pgvector: similarity search returns relevant guidelines within latency target; fallback to full-text search works.
- Scheduling: physician list filtered appropriately; unavailable physicians excluded.
- Ingestion: PDF upload → Textract → embedding → pgvector completes within SLA; failures handled gracefully with retry.
- Error handling: LLM timeout returns graceful fallback; pgvector failure falls back to keyword search; Textract failure marks job as failed.

### Reporting
- pytest coverage reports uploaded as CI artifacts.
- Test results summarized in PR checks.
- E2E video artifacts on failure.
- Ingestion pipeline metrics in admin dashboard.

## 05 Deployment Plan

### Environment Setup
- **Development**: Local `docker-compose up` or `uvicorn` + Vite dev server; PostgreSQL with pgvector extension enabled; MinIO for S3-compatible local object storage; seed database with synthetic guidelines and physician records.
- **Staging**: Mirror production infrastructure; use synthetic, non-PII health data; ingestion pipeline runs against test S3 bucket with sample PDFs.
- **Production**: HIPAA-aligned configuration; secrets injected via environment variables or vault; audit logging enabled; pgvector on production PostgreSQL.

### Ingestion Pipeline Deployment
- **Local dev**: FastAPI background task or Celery worker; MinIO for S3.
- **Staging/Production**: AWS Lambda (event-driven on S3 upload) or scheduled ECS task (cron); Textract invoked via boto3; results stored in production PostgreSQL.
- **Monitoring**: Ingestion job status table queried by admin dashboard; alerts on repeated failures.

### CI/CD Pipeline
- Lint + type check + unit tests on every PR.
- E2E tests on PRs touching `IOPHA-frontend/**` or `IOPHA-backend/**`.
- Build artifacts pushed to registry on merge to `main`.
- Production deploy triggered automatically or manually via `workflow_dispatch`.

### Deploy Process
1. Merge PR → CI pipeline passes → image built and tagged.
2. Deploy to staging → smoke tests pass.
3. Promote to production via manual approval or automated pipeline.
4. Run post-deploy smoke tests including ingestion pipeline health check.

### Rollback Strategy
- Docker image tags immutable; rollback = redeploy previous tag.
- Database migrations include `down` scripts in Alembic; pgvector index drops handled in down migrations.
- Feature flags toggled via config for gradual rollout.
- Ingestion pipeline: rollback = deactivate newly ingested guidelines (`isActive: false`); re-ingest previous version.

### Post-Deploy Verification
- Health check endpoints return 200.
- pgvector index queries validated with spot-check similarity searches.
- Ingestion pipeline: submit test PDF, verify completion and embedding quality.
- Error rate and latency dashboards checked for 15 minutes post-deploy.

## 06 Security & Performance

### Security
- **IAM & Access Control**: All services and jobs run under least-privilege IAM roles. AWS resources (Textract, S3) are accessed via scoped IAM policies. Application-level permissions enforce role-based access.
- **Input validation**: Strict validation on all API inputs; external data (e.g., Textract output) sanitized before processing.
- **Secrets management**: Secrets stored in environment variables or a secrets manager; no credentials in code or repo.
- **Dependency scanning**: Automated vulnerability scanning in CI for all dependencies.
- **Principle of least privilege**: Each component receives only the permissions required for its function. Network access is restricted to necessary endpoints.

### Performance
- **Targets**: Chat response <2s p95; pgvector guideline retrieval <500ms; page load <3s.
- **Optimization**: pgvector IVFFlat index for fast similarity search; CDN for frontend assets; database connection pooling; response streaming via WebSocket; guideline text cached in application memory for hot chunks.
- **Monitoring**: Prometheus and Grafana with AWS CloudWatch Logs integration for centralized metrics, dashboards, and alerting.
- **Scaling**: Horizontal scaling for backend API via container orchestration; read replicas for PostgreSQL if needed; ingest pipeline can be parallelized across documents.

### Observability
- **Logging**: Structured JSON logs from frontend (winston) and backend; ingestion job status transitions logged.
- **Metrics**: Request rate, error rate, duration (RED); cache hit rates; ingestion queue depth, job success/failure rate, Textract latency.
- **Alerting**: Alerts on error rate spikes, ingestion pipeline failures, or downstream service degradation.
