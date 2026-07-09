# Interactive Obesity Prevention Health Assistant (IOPHA)

## TL;DR

Despite accurate risk identification for obesity, timely intervention is lacking for high-risk users. The Interactive Obesity Prevention Health Assistant (IOPHA) bridges this gap by offering immediate, evidence-based prevention strategies and a seamless pathway to in-network clinical care, tailored to both user needs and the hospital organization. Targeting at-risk individuals, IOPHA maximizes engagement, improves health outcomes, and drives in-network patient acquisition.

## Goals

### Business Goals

- Increase in-network high-risk patient appointments by 25% within 6 months of deployment.
- Lower long-term care costs by enabling earlier intervention for at-risk users.
- Improve hospital brand engagement and patient retention via value-driven digital touchpoints.
- Increase premium wellness program enrollments resulting from assistant-driven recommendations.

### User Goals

- Empower users with timely, actionable, evidence-based obesity prevention strategies.
- Enable instant scheduling with in-network physicians, reducing friction to care.
- Provide a choice-driven experience for users preferring self-guided prevention or professional guidance.
- Ensure personalized, relevant advice grounded in each user's health profile and environment.

### Non-Goals

- Providing diagnoses or emergency interventions—assistant is for prevention and guidance, not acute care.
- Cross-network physician referrals; only in-network scheduling is supported.
- Long-term care management (e.g., ongoing remote coaching) beyond initial prevention and routing.

## User Stories

### Persona: At-Risk Adult User ("Carlos", 42, Pre-Diabetic)

- As an at-risk user, I want evidence-based dietary and lifestyle advice, so that I can make meaningful, healthy changes immediately.
- As an at-risk user, I want to schedule an appointment with a local physician quickly, so that I don't delay necessary treatment.
- As an at-risk user, I want my privacy respected and only see providers within the hospital I trust, so that I feel secure sharing my information.

### Persona: Medical Administrator

- As an admin, I want to monitor user engagement and conversion rates, so I can justify investment and identify improvement points.

### Persona: Hospital Physician

- As an in-network doctor, I want new patients routed to me with their risk profile attached, so that I can provide tailored consultations.

## Functional Requirements

### Interactive Health Guidance Engine (Priority: Highest)

- Personalized prevention recommendations grounded in the latest clinical guidance and user's lifestyle data.
- Dual-path user flow: instant in-network physician scheduling or self-guided tips.
- Real-time synthesis of responses—no generic or irrelevant advice.

### Hospital Directory Integration (Priority: High)

- Real-time querying of organization's physician and facility database.
- Location-aware routing: match users to nearest available providers in-network.

### Dynamic Personalization and Consent Handling (Priority: High)

- Context-driven responses based on entry point (e.g., Baylor vs. other hospitals).
- Robust consent and privacy gate for data usage.

### User Engagement Tracking & Analytics (Priority: Medium)

- Capture user decisions, paths taken, engagement duration, and outcomes.
- Admin dashboard summarizing usage, conversion, bounce, and follow-up rates.

### Scalable RAG Integration Layer (Priority: Medium)

- Dense vector encoding and retrieval logic for personalized data fusion.
- Model outputs explainable and auditable for clinical oversight.

## User Experience

### Entry Point & First-Time User Experience

- Users access the assistant after completing a lifestyle risk-assessment (e.g., on the Baylor website).
- The assistant introduces its function and obtains explicit consent for further engagement.
- Onboarding includes reassurance about data privacy, focused on in-network care.

### Core Experience

#### Step 1: System presents dual-path options

"Would you like expert guidance, schedule a doctor's appointment, or both?"

- Clear CTAs for both self-guided tips and scheduling.
- Tooltip explanations for each option.

#### Step 2: User selects an option

**If tips:**

- Presents top three evidence-based strategies (personalized, actionable, non-generic).
- Includes dynamic content like meal timing, exercise suggestions, etc.
- Options to see more, request clarification, or shift to scheduling.

**If scheduling:**

- System auto-fills user information and suggests matched in-network providers.
- Confirmation step before booking.

#### Step 3: Confirmation and next steps

- Shows summary, follow-up reminders, and ways to revisit or deepen engagement.

### Advanced Features & Edge Cases

- If user is hesitant or declines both options, prompt gentle reminders and offer low-effort, privacy-conscious actions.
- System adapts recommendations if scheduling fails or doctors are unavailable.

### UI/UX Highlights

- Intuitive dual-button response surfaces.
- High-contrast, accessible UI for older and visually-impaired users.
- Responsive across desktop/mobile.
- Clear data handling/privacy notices at each major touchpoint.

## Narrative

Carlos, a busy 42-year-old, takes a lifestyle survey on his hospital's website and receives an alert that he's at high risk for obesity-related complications. He's startled—diabetes runs in his family. Instantly, the health assistant appears, offering two supportive paths: three practical adjustments Carlos can start today and the option to see a trusted doctor down the street.

Hesitant to book immediately, Carlos tries the diet tips. The assistant delivers practical, science-backed changes—timing his meals better, adding in short daily walks, swapping sugary snacks for healthier alternatives. Sensing his interest, it gently suggests booking an appointment with Dr. Smith, who is nearby and in-network should he want a deeper evaluation.

Carlos feels both supported and not pressured; the experience is seamless, confidential, and—most importantly—actionable. Over the next weeks, Carlos notices improvement and eventually books that visit with Dr. Smith, trusting his hospital's commitment to prevention and care. This dual-pathway not only helps Carlos avoid costly chronic issues but also deepens his loyalty to the hospital network.

## Success Metrics

### User-Centric Metrics

- 50% of at-risk users engage with at least one preventive tip.
- At least 30% of at-risk users schedule a visit with an in-network provider after the assistant.
- High user satisfaction (>85% positive post-engagement survey).

### Business Metrics

- 25% increase in new high-risk patient appointments within 6 months.
- 15% growth in premium wellness program signups attributed to the assistant.
- Decreased long-term care costs by reducing progression to chronic disease.

### Technical Metrics

- 99% uptime during business hours.
- Median response time for recommendations <2 seconds.
- <0.1% rate of generic, ungrounded responses.

## Tracking Plan

- Daily/weekly engagement rates.
- Appointment bookings initiated via assistant.
- Preventive tips accessed/clicked.
- Abandonment/bounce rates.
- User consent provided/withheld.

## Technical Considerations

### Technical Needs

- Cloud-hosted RAG engine with secured APIs.
- Integration with EHR/physician directory for real-time scheduling.
- Scalable vector storage and retrieval system.
- User preference and consent store.

### Integration Points

- Hospital physician/facility directories.
- Risk model output streams.
- User authentication/consent modules.

### Data Storage & Privacy

- Encrypt all user data in transit and at rest.
- Compliance with HIPAA and organization-specific privacy rules.
- Audit trail for all user-facing responses and connections.

### Scalability & Performance

- Must handle spikes after large campaigns or during peak hours.
- Caching and batching for common guideline queries.

### Potential Challenges

- Data silos or inconsistently updated physician directories.
- Over-personalization risks (need for opt-out/easy privacy controls).
- Ensuring clinical validity and versioning of guideline content.

## Milestones & Sequencing

### Project Estimate

Medium: 2–4 weeks for MVP, including feedback cycles.

### Team Size & Composition

Small Team: 2–3 people (ML engineer, product/design lead, integration dev).

### Suggested Phases

#### Phase 1: MVP Build (2 weeks)

**Deliverables:** Consent flow, RAG-powered prevention response, initial directory integration (Product/Integration Dev).
**Dependencies:** Access to risk model output, clinical guideline base.

#### Phase 2: Scheduling & Analytics Integration (1 week)

**Deliverables:** Real-time physician matching, booking workflow, engagement dashboard (ML Engineer, Integration Dev).
**Dependencies:** Real-time API access to physician directory, analytics pipeline.

#### Phase 3: Iteration & Compliance Review (1 week)

**Deliverables:** User testing, HIPAA/privacy audit, edge case handling (Product, Security/Compliance).
**Dependencies:** Test user pool, compliance signoff.
