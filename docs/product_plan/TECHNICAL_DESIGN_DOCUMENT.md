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
- **API endpoints**: FastAPI REST routes + WebSocket `/api/v1/chat/sessions/:id/stream`.
- **Third-party integrations**: LLM API (HTTP), PostgreSQL + pgvector (psycopg/asyncpg), AWS Textract (boto3), S3 (boto3), Hospital directory DB (SQL).
- **Internal modules**: `app/api` (routes), `app/services` (RAG orchestration, directory matching, ingestion pipeline), `app/core` (auth, config, database), `app/workers` (cron / ingestion jobs).

### Document Ingestion Flow
1. Admin uploads clinical guideline PDF to S3 bucket.
2. S3 event notification or cron triggers ingestion job.
3. Backend creates `GuidelineIngestionJob` record with `status: pending`.
4. AWS Textract processes the document; raw text extracted.
5. Text is chunked (e.g., 512-token windows with overlap).
6. Each chunk is embedded via OpenAI `text-embedding-3-small`.
7. Embeddings are upserted into `ClinicalGuideline` table in pgvector with `organizationId` and metadata.
8. Job marked `completed`; guideline becomes available for RAG retrieval.
9. On failure, error logged in `GuidelineIngestionJob.errorMessage`; retry scheduled.

### User Interface
- Dual-action chat interface: immediate tips and nearby physician suggestions side-by-side.
- Accessible, high-contrast design for older and visually-impaired users.
- Responsive layout for desktop and mobile.

## 03 Data Model

### Entities
```
User
  id: uuid (PK)
  email: text (unique, indexed)
  name: text
  organizationId: uuid (FK)
  role: enum(patient, admin)
  consentGiven: boolean
  consentTimestamp: timestamptz
  createdAt: timestamptz

Organization
  id: uuid (PK)
  name: text
  domain: text (unique)
  settings: jsonb
  createdAt: timestamptz

RiskProfile
  id: uuid (PK)
  userId: uuid (FK, indexed)
  bmi: numeric
  lifestyleData: jsonb
  riskScore: numeric
  riskLevel: enum(low, medium, high, critical)
  detectedAt: timestamptz

ClinicalGuideline
  id: uuid (PK)
  title: text
  content: text
  embedding: vector(1536) — pgvector in PostgreSQL
  category: text
  organizationId: uuid (FK, nullable, indexed)
  version: text
  isActive: boolean
  sourceDocumentUri: text — S3 path or URL to original PDF
  createdAt: timestamptz

Physician
  id: uuid (PK)
  organizationId: uuid (FK, indexed)
  name: text
  specialty: text
  facilityId: uuid (FK)
  availability: jsonb
  isActive: boolean
  createdAt: timestamptz

Facility
  id: uuid (PK)
  organizationId: uuid (FK, indexed)
  name: text
  address: text
  city: text
  state: text
  zip: text
  latitude: numeric
  longitude: numeric
  phone: text
  createdAt: timestamptz

ConversationSession
  id: uuid (PK)
  userId: uuid (FK, indexed)
  organizationId: uuid (FK, indexed)
  startedAt: timestamptz
  endedAt: timestamptz
  outcome: enum(tips-only, scheduled, declined, pending)

Message
  id: uuid (PK)
  sessionId: uuid (FK, indexed)
  role: enum(user, assistant, system)
  content: text
  metadata: jsonb
  createdAt: timestamptz

GuidelineIngestionJob
  id: uuid (PK)
  sourceDocumentUri: text
  status: enum(pending, processing, completed, failed)
  textractJobId: text (nullable)
  errorMessage: text (nullable)
  processedAt: timestamptz (nullable)
  createdAt: timestamptz
```

### Relationships
- User → Organization: Many-to-one
- User → RiskProfile: One-to-many
- User → ConversationSession: One-to-many
- Organization → Facility: One-to-many
- Organization → Physician: One-to-many
- Facility → Physician: One-to-many
- ConversationSession → Message: One-to-many
- User ↔ ClinicalGuideline: Relationship via vector similarity (semantic join)
- ClinicalGuideline → GuidelineIngestionJob: One-to-one via ingestion process

### Storage
- **Database**: PostgreSQL with pgvector extension (Neon, Supabase, AWS RDS with pgvector, or self-hosted). Relational data and vector embeddings co-located.
- **Vector Store**: pgvector for clinical guideline embeddings and user-profile vectors. IVFFlat index for cosine similarity search.
- **Caching**: Redis (TO BE DETERMINED) for frequent guideline lookups and session state.
- **Blob storage**: AWS S3 or compatible for raw clinical guideline PDFs.

### Data Flow — RAG Chat
1. User sends message via WebSocket.
2. Backend encodes message + user risk profile into vector.
3. pgvector retrieves top-k clinical guidelines filtered by `organizationId` (or global guidelines if no org-specific match).
4. Backend queries hospital directory for nearby in-network physicians.
5. LLM synthesizes response using retrieved context and physician options.
6. Response streamed back to frontend; message and metadata persisted to PostgreSQL.

### Data Flow — Document Ingestion
1. PDF uploaded to S3 by admin or automated process.
2. Trigger: S3 event (preferred) or cron job (fallback).
3. Backend calls AWS Textract to extract structured text.
4. Text is split into chunks (512 tokens, 128-token overlap) with metadata (organizationId, category, version).
5. Each chunk is sent to embedding model; vectors stored in `ClinicalGuideline.embedding` via pgvector upsert.
6. Job status updated; failures retried up to 3 times with exponential backoff.

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
- Auth: invalid tokens return 401; cross-organization queries return 403.
- RAG: high-risk user receives guideline-based response; no generic content when pgvector is available.
- pgvector: similarity search returns relevant guidelines within latency target; fallback to full-text search works.
- Scheduling: physician list filtered by organization; unavailable physicians excluded.
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
- **Monitoring**: `GuidelineIngestionJob` table queried by admin dashboard; alerts on repeated failures.

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
- Sentry alert thresholds reviewed.
- Error rate and latency dashboards checked for 15 minutes post-deploy.

## 06 Security & Performance

### Security
- **Authentication & Authorization**: JWT + httpOnly cookies; per-route FastAPI dependencies; organization-scoped query filters.
- **Input validation**: Pydantic schemas enforce strict types on all API inputs; Textract output sanitized before embedding.
- **Secrets management**: Environment variables or host-level secrets manager; no secrets in repo.
- **Dependency scanning**: Bandit (Python) + pip-audit (Python) in CI; npm audit (frontend) in CI.
- **Document handling**: Uploaded PDFs scanned for malware; limited to approved MIME types; stored in encrypted S3.
- **OWASP considerations**:
  - A01: Broken access control → Organization scoping on all queries; ingestion jobs require internal auth.
  - A02: Cryptographic failures → TLS 1.3, encrypted secrets at rest, S3 server-side encryption.
  - A03: Injection → Parameterized queries via SQLAlchemy; prompt injection mitigation via system prompts and context filtering.
  - A07: Auth failures → Rate limiting, MFA (TO BE DETERMINED).
  - A08: Data integrity failures → CI dependency auditing; Textract job verification before upsert.

### Performance
- **Targets**: Chat response <2s p95; pgvector guideline retrieval <500ms; page load <3s.
- **Optimization**: pgvector IVFFlat index for fast similarity search; CDN for frontend assets; database connection pooling; response streaming via WebSocket; guideline text cached in application memory for hot chunks.
- **Monitoring**: Sentry for errors; custom metrics for latency and throughput; ingestion job duration tracked.
- **Scaling**: Horizontal scaling for backend API via container orchestration; read replicas for PostgreSQL if needed; ingest pipeline can be parallelized across documents.

### Observability
- **Logging**: Structured JSON logs with request ID, user ID (anonymized), latency; ingestion job status transitions logged.
- **Metrics**: Request rate, error rate, duration (RED); cache hit rates; ingestion queue depth, job success/failure rate, Textract latency.
- **Alerting**: PagerDuty / Slack alerts on error rate spikes, ingestion pipeline failures, or downstream service degradation (Textract, LLM, pgvector).
