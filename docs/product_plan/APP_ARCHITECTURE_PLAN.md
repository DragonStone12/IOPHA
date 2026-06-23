# IOPHA: App Architecture Plan

## 01 System Overview

An AI-powered health assistant that delivers personalized, evidence-based obesity prevention guidance and routes high-risk users to in-network medical professionals immediately after risk detection. The assistant operates inside hospital and healthcare organization ecosystems, delivering dual-pathway interventions: self-directed prevention tips and direct care scheduling.

- **Type**: Monorepo — Separate frontend (React SPA) and backend (FastAPI API) deployed independently.
- **Key components**: Frontend SPA, Backend API, PostgreSQL (relational + pgvector), LLM Orchestration Layer, Hospital Directory Service, Session Store, Document Ingestion Pipeline (Textract → pgvector).

### System Diagram

```
User Browser
   │ HTTPS/WSS
   ▼
CDN / Frontend Host (Vercel / Cloudflare Pages)
   │ REST/WebSocket
   ▼
API Gateway / Backend Host (Railway / Fly / AWS ECS)
   │
   ├──► PostgreSQL (pgvector) — Relational data + clinical guideline embeddings
   ├──► Hospital Directory DB (PostgreSQL) — Physician/facility records
   │
   ├──► LLM Provider (OpenAI / Anthropic / Azure OpenAI) — Response synthesis
   │
   ▼
Document Ingestion Pipeline (Scheduled / Event-driven)
   │
   ├──► S3 / Object Storage — Raw clinical PDFs / scanned documents
   ├──► AWS Textract / OCR Engine — Structured text extraction
   ├──► Embedding Generator (OpenAI text-embedding-3 / Cohere) — Vector encoding
   └──► pgvector (via ALTER TABLE / upsert) — Guidelines stored as vector embeddings
```

## 03 Data Model

Core entities live in the primary relational store (users, organizations, risk profiles, physicians, facilities, sessions, messages) and a guidelines table augmented with vector search for semantic retrieval. A jobs table tracks document processing status. All tenant-scoped tables carry an organization identifier for multi-tenancy. Relevant indexes support lookups by user, organization, session, and vector similarity.

## 04 API Design

The backend exposes REST endpoints for auth, user management, risk assessments, chat, directory queries, and appointments, plus an internal ingestion API for the document pipeline. All client routes are auth-gated; ingestion routes are internal-only. Rate limiting is applied per route class, and pagination uses `limit`/`offset` with a standard envelope. Error responses follow a consistent JSON structure with code, message, and details.
```

## 05 Auth & Permissions

### Authentication
- **Provider**: TO BE DETERMINED — evaluating Supabase Auth vs. custom JWT with FastAPI.
- **Methods**: Email/password, OAuth (Google, GitHub), Magic link.
- **Session handling**: JWT access tokens (15 min) + refresh tokens (7 days) stored in httpOnly cookies.

### Authorization
- **Roles**:
  - `patient`: Access own data, chat, schedule appointments
  - `admin`: Manage organization physicians, facilities, guidelines; view ingestion job status
- **Enforcement**: Per-route dependency injection via FastAPI dependencies; organization-scoped queries enforce data isolation at the service layer.
- **Public routes**: Auth registration, login, and token refresh endpoints are publicly accessible.

### Multi-tenancy
- Organization-scoped data isolation via organization identifiers on all primary entities.
- Frontend derives organization from user profile at login; all subsequent requests are filtered by the user's linked organization.
- Clinical guideline embeddings are filtered by organization at query time, defaulting to global guidelines when no org-specific match is available.
- Cross-organization data access is prohibited at the database query level.

## 06 Third-Party Services

### LLM Provider
- **Service**: OpenAI / Anthropic / Azure OpenAI — Response synthesis and embedding generation.
- **SDK/Library**: `openai` Python SDK or `litellm` for provider abstraction.
- **Config**: `LLM_API_KEY`, `LLM_MODEL` (e.g., `gpt-4o-mini`), `EMBEDDING_MODEL` (e.g., `text-embedding-3-small`), `LLM_PROVIDER`
- **Failure handling**: Graceful fallback to cached guideline snippets if LLM is unavailable; response degraded but not blocked.

### PostgreSQL + pgvector
- **Service**: PostgreSQL with pgvector extension — Primary relational store and vector similarity search for clinical guidelines.
- **SDK/Library**: SQLAlchemy with pgvector support; vector operations via the pgvector client.
- **Config**: `DATABASE_URL` (PostgreSQL connection string)
- **Failure handling**: If vector similarity search fails, fall back to full-text search on guideline content using native database text search.

### Hospital Directory Service
- **Service**: Internal PostgreSQL database with organization-specific physician and facility records.
- **SDK/Library**: SQLAlchemy / raw SQL via asyncpg.
- **Config**: `DATABASE_URL`
- **Failure handling**: If directory lookup fails, return empty physician list and prompt user to contact hospital directly.

### AWS Textract (Document Ingestion)
- **Service**: AWS Textract — OCR and structured text extraction from scanned clinical guidelines (PDFs).
- **SDK/Library**: `boto3` Python SDK.
- **Config**: `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET_GUIDELINES`
- **Failure handling**: If Textract fails, ingestion job marked as `failed` with error details; retry with exponential backoff; alert admin if repeated failures.

### S3 / Object Storage
- **Service**: AWS S3 or compatible — Stores raw uploaded clinical guideline documents.
- **SDK/Library**: `boto3`
- **Config**: `S3_BUCKET_GUIDELINES`
- **Failure handling**: Queue uploads for retry; block new guideline activation if source document is missing.

### Embedding Generator
- **Service**: OpenAI `text-embedding-3-small` or equivalent — Converts extracted text into vector embeddings.
- **SDK/Library**: `openai` Python SDK.
- **Config**: `EMBEDDING_MODEL`, `LLM_API_KEY`
- **Failure handling**: Retry transient errors; if persistent, mark ingestion job as failed and stop pipeline.

### Email / Notifications
- **Service**: TO BE DETERMINED — evaluating Resend, SendGrid, or Postmark.
- **SDK/Library**: Corresponding provider SDK or `resend` Python client.
- **Config**: `EMAIL_API_KEY`, `EMAIL_FROM`
- **Failure handling**: Queue notifications for retry; log failure but do not block core experience.

### Monitoring & Error Tracking
- **Service**: Sentry — Backend error tracking.
- **SDK/Library**: `sentry-sdk[fastapi]`
- **Config**: `SENTRY_DSN`
- **Failure handling**: If Sentry is down, errors are logged locally; no user impact.

## 07 Frontend Architecture

### Tech Choices
- **Framework**: React 18 + TypeScript + Vite 5
- **Component library**: TO BE DETERMINED — evaluating shadcn/ui or Radix primitives.
- **Styling**: TO BE DETERMINED — evaluating Tailwind CSS or CSS Modules.
- **State management**: TO BE DETERMINED — evaluating React Query (TanStack Query) for server state and Zustand for client state.

### Page Structure
- `/` — Landing page (organization-branded)
- `/app` — Main chat interface
- `/app/sessions/:id` — Chat session view
- `/app/schedule` — Physician scheduling flow
- `/settings` — User profile and consent management
- `/login` — Authentication
- `/register` — New user registration

### Data Fetching Strategy
- Server components: Not applicable (SPA architecture).
- Client components: React Query for all server state; optimistic updates for chat messages.
- Caching: Stale-while-revalidate for guidelines and physician directories.
- Global error handling: React Query error boundaries + Sentry integration.

## 08 Infrastructure & Deployment

### Hosting
- **Frontend**: TO BE DETERMINED — Vercel, Netlify, or Cloudflare Pages.
- **Backend**: TO BE DETERMINED — Railway, Fly.io, or AWS Fargate.
- **Database**: TO BE DETERMINED — Neon (PostgreSQL + pgvector), Supabase, or AWS RDS with pgvector extension.
- **Object Storage**: AWS S3 or compatible for guideline document storage.

### Document Ingestion Infrastructure
- ** Ingestion Service**: FastAPI scheduled task or AWS Lambda triggered on S3 upload events.
- **Pipeline**: S3 upload → Textract OCR → text chunking → embedding generation → pgvector upsert.
- **Scheduling**: Cron-based or event-driven (S3 event notifications to Lambda).
- **Monitoring**: Ingestion job status table with admin dashboard visibility.

### CI/CD Pipeline
- GitHub Actions workflows scoped by path:
  - `.github/workflows/ci-frontend.yml` — triggers on `IOPHA-frontend/**` changes; runs lint + npm audit.
  - `.github/workflows/ci-backend.yml` — triggers on `IOPHA-backend/**` changes; runs Bandit + pip-audit.
  - `.github/workflows/deployment.yml` — manual or main-branch deploy for remaining paths.
- Preview deployments for PRs via frontend and backend hosts.
- Production deployment triggered by merge to `main`.

### Environments
- **Development**: Local Docker Compose or `uvicorn` + Vite dev server; seed data in local PostgreSQL with pgvector; local Textract emulator or sample documents in S3-compatible storage (e.g., MinIO).
- **Staging**: Mirrors production infra; uses synthetic health data; ingestion pipeline runs against test S3 bucket.
- **Production**: Full infra with HIPAA-compliant config; audit logging enabled; secrets in vault or host secrets manager.

### Environment Variables

| Category | Variable | Secret | Description |
|----------|----------|--------|-------------|
| Auth | `JWT_SECRET` | Yes | HMAC signing key |
| Auth | `AUTH_PROVIDER_URL` | No | Supabase / OAuth issuer URL |
| Database | `DATABASE_URL` | Yes | PostgreSQL connection string |
| Vector DB | `PGVECTOR_DIMENSION` | No | Embedding dimension (default 1536) |
| AWS | `AWS_ACCESS_KEY_ID` | Yes | AWS credential for Textract/S3 |
| AWS | `AWS_SECRET_ACCESS_KEY` | Yes | AWS secret key |
| AWS | `AWS_REGION` | No | AWS region (e.g., us-east-1) |
| AWS | `S3_BUCKET_GUIDELINES` | No | S3 bucket for guideline documents |
| LLM | `LLM_API_KEY` | Yes | OpenAI / Anthropic key |
| LLM | `LLM_MODEL` | No | Model identifier |
| Email | `EMAIL_API_KEY` | Yes | Resend / SendGrid key |
| Monitoring | `SENTRY_DSN` | Yes | Sentry project DSN |
| App | `APP_ENV` | No | development / staging / production |
| App | `CORS_ORIGINS` | No | Allowed frontend origins |
