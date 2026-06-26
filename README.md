# IOPHA: Predictive Obesity Risk Health Assistant

A monorepo containing the Interactive Obesity Prevention Health Assistant, powered by Retrieval-Augmented Generation (RAG).

## Repository Structure

```
├── IOPHA-frontend/     # React/TypeScript application
├── IOPHA-backend/      # FastAPI application
├── infra/              # Infrastructure as Code (Terraform/CDK)
└── docs/               # Architecture diagrams and compliance notes
```

## The Problem

Predictive models identify users at high risk for obesity, but early detection alone is insufficient. Without timely intervention, individuals face severe long-term complications including diabetes and heart disease, significantly increasing healthcare costs. There is a critical gap between identifying risk and providing immediate, actionable prevention. Additionally, high-risk users lack a seamless pathway to schedule appointments with in-network medical professionals or receive reliable guidance if they hesitate to seek care.

## Our Solution

Deploying an interactive health assistant immediately after risk detection provides a dual-pathway for intervention:

- **Care Routing**: Directly connects users to the nearest available doctor within their hospital's network (e.g., Baylor users connect to Baylor physicians).
- **Immediate Guidance**: Delivers evidence-based health information for users who choose not to see a physician right away.

By offering both options, the system ensures no high-risk individual is left without support, improving long-term outcomes and creating monetization pathways through in-network visits and preventative programs.

## How It Works: RAG Architecture

1. **Encoding**: A text encoder converts the user's question and risk profile into a dense vector.
2. **Retrieval**: The system performs nearest neighbor search across two distinct databases:
   - **Clinical Guidelines Database**: Retrieves verified preventative care guidelines and the user's stored lifestyle constraints.
   - **Physician Directory Database**: Retrieves the closest available physicians and facilities within the specific hospital network, determined by the website domain the user entered from.
3. **Synthesis**: The language model synthesizes the retrieved information to generate a comprehensive, dual-option response.

### Example Flow

A user completes a health survey on Baylor's website and triggers a high-risk alert. When they ask how to manage their weight, the system retrieves clinical guidelines on obesity prevention and cross-references the user's location with the Baylor physician directory. The response includes:

> "To help manage your risk, here are three evidence-based dietary adjustments you can start today, such as adjusting your meal timing to align with your waking hours. Additionally, because early intervention is highly effective, we recommend a professional consultation. I have located Dr. Smith at the closest Baylor facility, just 2 miles from your location. Would you like me to schedule an appointment with Dr. Smith, provide you with more daily health tips, or both?"

## Business Impact

- **Improved Outcomes**: Reduces the likelihood of costly chronic disease management through early intervention.
- **Increased Engagement**: Accommodates all user comfort levels with both professional care connections and immediate self-directed advice.
- **Monetization**: Creates a direct pathway to revenue through in-network clinical visits and premium preventative wellness programs.

## Documentation

- **[System Architecture (HLD)](docs/ARCHITECTURE.md)** - High-level design, system overview, architecture diagram, compliance & HIPAA posture
- **[Technical Design (LLD)](docs/TECHNICAL_DESIGN.md)** - Low-level implementation details, API specs, database schema, testing strategy

## Quick Start

### Local Development

```bash
# Start all services (frontend, backend, database)
docker-compose up

# Frontend development
cd IOPHA-frontend
npm install
npm run dev

# Backend development
cd IOPHA-backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Run tests
npm run test:e2e  # Frontend E2E (Cypress)
pytest             # Backend unit tests
```

### Environment Variables

Copy `.env.example` and configure:
- `DATABASE_URL` - PostgreSQL connection string
- `LLM_API_KEY` - OpenAI/Bedrock API key
- `JWT_SECRET` - JWT signing key
- `AWS_*` - AWS credentials for Textract/S3

## Development

### Frontend (IOPHA-frontend)

Husky git hooks are configured for code quality:

```bash
npm install  # installs dependencies and husky automatically via prepare script
```

Pre-commit hook runs lint-staged to lint and format staged files.

### Backend (IOPHA-backend)

Pre-commit hooks configured via `.pre-commit-config.yaml`:

```bash
pip install pre-commit
pre-commit install
```
