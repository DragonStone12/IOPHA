# IOPHA Chat & Appointment Booking Flow: Feature Implementation Spec

**Feature:** Interactive Obesity Prevention Health Assistant (IOPHA) – Core Engagement & Booking Module
**Version:** 1.0 (MVP)
**Status:** Ready for Development

## 01 Feature Summary

The IOPHA Chat & Appointment Booking Flow is a conversational interface that bridges the gap between obesity risk identification and clinical intervention. It provides at-risk users with personalized, evidence-based prevention strategies (Nutrition, Exercise, Sleep) via a RAG-powered chat engine and enables seamless scheduling with in-network physicians through an integrated booking workflow. This feature directly supports the business goal of increasing in-network high-risk patient appointments by 25% while empowering users with immediate self-guided care options.

### Scope

**In scope:**
- Landing page with Risk Profile sidebar and initial AI greeting.
- Four primary chat flows: Weight & Nutrition Tips, Find a Doctor, Exercise Guidance, Sleep & Recovery.
- Structured advice cards (numbered tips) and Physician Recommendation cards.
- End-to-end appointment booking flow: Time selection → Confirmation form → Success state → Chat integration.
- Context-aware follow-up action chips after each response.
- Cypress Component Testing and Cucumber BDD tests for all flows.

**Out of scope:**
- User authentication / login flow (assumes pre-authenticated session or guest mode).
- Payment processing or insurance verification.
- Telehealth/video visit functionality.
- Admin dashboard for analytics (separate epic).
- Multi-language support.

**Prerequisites:**
- IOPHA Resources component library available and documented.
- Backend API endpoints for RAG responses and physician directory search.
- Booking API endpoint for slot reservation and confirmation.
- User context (name, age, location, BMI, risk factors) available via props or global state.

**Depends on:**
- RAG pipeline returning structured JSON responses (not raw text).
- Physician directory API with real-time availability.
- Email service for confirmation notifications.

## 02 Acceptance Criteria

### Must-Have (P0)

- [ ] Landing Page Rendering: User lands on a page displaying their specific Risk Score (e.g., 78/100), Contributing Factors list, and "Quick Start" navigation links matching the Figma design.
- [ ] Dynamic Greeting: The initial AI message correctly interpolates the user's name, risk score, and hospital network (e.g., "Baylor Scott & White Health") without generic placeholders.
- [ ] Structured Advice Rendering: Selecting "Weight & nutrition tips", "Exercise guidance", or "Sleep & recovery" renders exactly 3 numbered tip cards with correct titles and descriptions derived from the API payload.
- [ ] Physician Card Display: Selecting "Find a doctor" or receiving a recommendation renders a PhysicianCard with Name, Specialty, Distance, Rating, Next Available Slot, and a functional "Book" button.
- [ ] Booking Flow Navigation: Clicking "Book" transitions the user to the "Select Appointment Time" view; selecting a date and time enables the "Continue to Confirmation" button.
- [ ] Form Validation: The "Confirm Your Appointment" form prevents submission if Name, Email, or Phone fields are empty or invalid, displaying inline error messages.
- [ ] Booking Confirmation: Successful form submission triggers the "Appointment Confirmed" success modal AND injects a confirmation summary card into the chat history.
- [ ] Follow-up Chips: Every AI response includes a row of context-aware chips (e.g., "Book Dr. Chen", "Get health tips first") that trigger the correct subsequent flow.

### Should-Have (P1)

- [ ] Pre-filled Patient Data: If user context is available, the confirmation form auto-populates Name, Email, and Phone fields.
- [ ] Calendar State Management: Navigating "Back" from the confirmation form preserves the previously selected date/time in the calendar view.
- [ ] Loading States: All API interactions (RAG response, Slot fetch, Booking submit) display appropriate loading skeletons or spinners to prevent UI freezing.
- [ ] Error Handling: Failed booking attempts (e.g., slot taken) display a non-blocking toast error and return the user to the time selection screen.

### Nice-to-Have (P2)

- [ ] Keyboard Navigation: Calendar and time slots are fully navigable via arrow keys and Enter/Space.
- [ ] Smooth Transitions: CSS transitions exist between chat states and booking modal steps (fade/slide).
- [ ] Tooltip Explanations: Hovering over "Risk Score" or "Contributing Factors" shows brief explanatory tooltips.

## 03 User Flow

### Happy Path

1. Entry Point: User completes risk survey → Lands on Landing Page → Sees "78/100 High Risk" and "Welcome, Sarah..." message.
2. Action (Self-Guided): User clicks "Weight & nutrition tips" chip → System renders intro text + 3 Tip Cards + Follow-up chips.
3. Action (Clinical): User clicks "Find a doctor" → System renders Physician List → User clicks "Book" on Dr. Chen.
4. Booking Step 1: Select Time View opens → User selects "June 26" → User selects "04:00 PM" → "Continue" button activates.
5. Booking Step 2: User clicks "Continue" → Confirm Form View opens → User reviews summary (pre-filled) → Clicks "Confirm Appointment".
6. Result: Success Modal appears ("Appointment Confirmed!") → User closes modal (or auto-close).
7. Next Step: Chat updates with "Your appointment has been confirmed" message + Green Summary Card + New chips ("Nutrition tips", "Exercise guidance").

### Alternate Paths

**Path B (Pivot):** User is on "Exercise Guidance" screen → Clicks "Find a doctor" chip → System renders Physician List immediately.

**Path C (Abort Booking):** User is on "Select Time" screen → Clicks "Back to Health Assistant" → Returns to main chat interface; booking state is discarded.

**Path D (Change Details):** User is on "Confirm Form" → Clicks "Change date or time" → Returns to "Select Time" view with previous selection preserved.

## 04 Edge Cases & Error States

### Input Validation

- Empty Required Fields: Submitting confirmation form with missing Name/Email/Phone → Inline red border + "This field is required" text below input.
- Invalid Email: Entering "user@com" → "Please enter a valid email address" error on blur/submit.
- Invalid Phone: Entering alphabetic characters → "Please enter a valid 10-digit phone number" error.

### System Errors

- No Slots Available: Calendar loads but no times shown for selected date → Display "No appointments available for this date. Please select another day." inside the Time Slot panel.
- Slot Taken (Race Condition): User clicks "Confirm" but slot was just booked by another user → Toast notification: "Sorry, this time slot is no longer available." → Redirect to Time Selection.
- RAG Timeout: API takes >5s to return tips → Show typing indicator → After 10s, show "We're having trouble connecting. Please try again." with retry button.
- Network Failure: Offline during booking → Disable "Confirm" button → Show "Connection lost. Check your internet and try again." banner.

### Permission & State

- Stale Session: User token expires mid-flow → Redirect to Login → Return to current booking step upon re-auth.
- Missing User Context: Guest user lands on page → Hide "Sarah Mitchell" card → Show generic "Guest" avatar + "Complete your profile" CTA in sidebar.
- Direct URL Access: User navigates directly to /booking/confirm without selecting a doctor → Redirect to Landing Page with error toast.

## 05 Technical Approach

### Files to Create/Modify

- src/components/chat/LandingPage.tsx — New composite component for sidebar + initial chat state.
- src/components/chat/messages/TipCard.tsx — Reusable numbered advice card component.
- src/components/chat/messages/PhysicianCard.tsx — Provider listing component with Book CTA.
- src/components/booking/TimeSelector.tsx — Calendar + Time slot grid + Sticky footer.
- src/components/booking/ConfirmationForm.tsx — Patient info form + Summary sidebar.
- src/components/booking/SuccessModal.tsx — Full-screen confirmation overlay.
- src/components/chat/ChatInterface.tsx — Modified to handle routing between Chat and Booking views.
- src/lib/api/iopha.ts — New API client methods for getGuidance, searchProviders, bookAppointment.
- cypress/e2e/booking-flow.cy.ts — E2E test suite.
- cypress/component/*.cy.tsx — Component tests for all new UI elements.

### Data Flow

1. Chat Interaction: UI sends POST /api/chat/message with { intent: "nutrition_tips", userId: "..." }.
2. RAG Processing: Backend retrieves guidelines → LLM generates structured JSON → Returns { type: "advice_list", content: [...], followUpChips: [...] }.
3. Booking Initiation: UI sends GET /api/providers/{id}/slots?date=... → Returns available times.
4. Reservation: UI sends POST /api/bookings with { providerId, slotId, patientData }.
5. Confirmation: Backend creates record → Triggers email → Returns { bookingId, summary }.
6. UI Update: Frontend adds type: "booking_confirmation" message to chat array.

### New Dependencies

- react-day-picker — For accessible calendar selection.
- zod — For frontend form validation schema matching backend expectations.
- cypress-cucumber-preprocessor — For BDD test execution.

## 06 Dependencies & Risks

### Dependencies

- Upstream: Risk Assessment Survey completion (triggers entry).
- Downstream: Email Notification Service (confirmation emails).
- External: Baylor Scott & White Physician Directory API (real-time sync required).

### Technical Risks

- Performance: Calendar rendering with 30+ days of slot data could lag. Mitigation: Lazy load slots only when date is selected.
- **For more information, read the security document.** ([docs/SECURITY.md](SECURITY.md))
- PII (Name, Phone, Email) in booking form. Mitigation: Ensure HTTPS only; do not log form payloads; sanitize inputs server-side.
- Data Integrity: Double-booking risk. Mitigation: Optimistic locking or atomic DB transactions on slot reservation.
- Accessibility: Custom calendar components often fail WCAG. Mitigation: Use established library primitives; audit with axe-core.

### Rollout Strategy

- Feature Flag: iopha_booking_v1 — Defaults to OFF.
- Staged Rollout: Internal QA → Beta (5% of at-risk users) → GA (100%).
- Rollback Plan: Toggle flag OFF → Users redirected to static "Contact Us" page instead of booking flow.

## 07 Test Plan

### Manual Testing

- Happy Path: Complete full flow from Landing → Nutrition Tips → Find Doctor → Book → Confirm → Verify Chat Update.
- Validation: Attempt to submit booking form with empty fields, invalid email, and short phone number.
- Navigation: Test "Back" buttons at every stage; verify state preservation vs. reset logic.
- Mobile: Verify responsive layout on iPhone SE (375px width) and iPad (768px width).
- Accessibility: Tab through entire booking flow; verify screen reader announces slot selections and form errors.

### Automated Tests

**Unit Tests:**
- TipCard: Renders correct number badge and title.
- PhysicianCard: Formats distance/rating correctly.
- ValidationSchema: Rejects invalid emails/phones.

**Integration Tests:**
- POST /api/bookings: Returns 201 on valid payload; 409 on duplicate slot.
- GET /api/providers/{id}/slots: Returns sorted time slots.

**E2E Tests (Cypress):**
- booking-flow.cy.ts: Full end-to-end booking scenario.
- chat-navigation.cy.ts: Switching between tips/doctors/exercise/sleep.

**Component Tests (Cypress):**
- TimeSelector.cy.tsx: Select date → Verify time slots update.
- ConfirmationForm.cy.tsx: Submit empty → Verify errors appear.

### Regression Checks

- Verify Landing Page risk score bar still animates correctly.
- Verify Chat History persists after page refresh.
- Check Sentry for new errors related to zod validation or calendar rendering.
- Verify Analytics events fire for chat_intent_selected and booking_confirmed.