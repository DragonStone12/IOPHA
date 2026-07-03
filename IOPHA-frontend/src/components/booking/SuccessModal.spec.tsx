import { SuccessModal } from "./SuccessModal";
import type { Physician } from "../NutritionResponse/PhysicianCard";

const MOCK_PHYSICIAN: Physician = {
  id: "dr-chen",
  name: "Dr. Emily Chen, MD",
  specialty: "Obesity & Metabolic Medicine",
  distance: "1.8 miles",
  rating: 4.9,
  reviewCount: 234,
  nextAvailable: "Today, 3:30 PM",
  facility: "Baylor University Medical Center",
  imageUrl:
    "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=200&h=200&fit=crop&auto=format",
};

const MOCK_DATE = new Date(2026, 5, 26);
const MOCK_TIME = "04:00 PM";
const MOCK_PATIENT_NAME = "Sarah Mitchell";
const MOCK_PATIENT_EMAIL = "sarah@example.com";
const MOCK_PATIENT_PHONE = "5551234567";

describe("SuccessModal Component", () => {
  beforeEach(() => {
    cy.clock(new Date(2026, 5, 26, 15, 0, 0));
  });

  afterEach(() => {
    cy.clock().then((clock) => clock.restore());
  });

  it("should render 'Appointment Confirmed!' title", () => {
    cy.mount(
      <SuccessModal
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
        patientName={MOCK_PATIENT_NAME}
        patientEmail={MOCK_PATIENT_EMAIL}
        patientPhone={MOCK_PATIENT_PHONE}
        onClose={() => {}}
      />,
    );
    cy.contains("Appointment Confirmed!").should("be.visible");
  });

  it("should render success message about confirmation email", () => {
    cy.mount(
      <SuccessModal
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
        patientName={MOCK_PATIENT_NAME}
        patientEmail={MOCK_PATIENT_EMAIL}
        patientPhone={MOCK_PATIENT_PHONE}
        onClose={() => {}}
      />,
    );
    cy.contains(
      "You will receive a confirmation email shortly with all the details.",
    ).should("be.visible");
  });

  it("should display physician name in summary", () => {
    cy.mount(
      <SuccessModal
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
        patientName={MOCK_PATIENT_NAME}
        patientEmail={MOCK_PATIENT_EMAIL}
        patientPhone={MOCK_PATIENT_PHONE}
        onClose={() => {}}
      />,
    );
    cy.contains("Dr. Emily Chen, MD").should("be.visible");
  });

  it("should display physician specialty in summary", () => {
    cy.mount(
      <SuccessModal
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
        patientName={MOCK_PATIENT_NAME}
        patientEmail={MOCK_PATIENT_EMAIL}
        patientPhone={MOCK_PATIENT_PHONE}
        onClose={() => {}}
      />,
    );
    cy.contains("Obesity & Metabolic Medicine").should("be.visible");
  });

  it("should display selected date and time in summary", () => {
    cy.mount(
      <SuccessModal
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
        patientName={MOCK_PATIENT_NAME}
        patientEmail={MOCK_PATIENT_EMAIL}
        patientPhone={MOCK_PATIENT_PHONE}
        onClose={() => {}}
      />,
    );
    cy.contains("Friday, June 26, 2026 at 04:00 PM").should("be.visible");
  });

  it("should display facility location in summary", () => {
    cy.mount(
      <SuccessModal
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
        patientName={MOCK_PATIENT_NAME}
        patientEmail={MOCK_PATIENT_EMAIL}
        patientPhone={MOCK_PATIENT_PHONE}
        onClose={() => {}}
      />,
    );
    cy.contains("Baylor University Medical Center").should("be.visible");
  });

  it("should display patient name in summary", () => {
    cy.mount(
      <SuccessModal
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
        patientName={MOCK_PATIENT_NAME}
        patientEmail={MOCK_PATIENT_EMAIL}
        patientPhone={MOCK_PATIENT_PHONE}
        onClose={() => {}}
      />,
    );
    cy.contains("Sarah Mitchell").should("be.visible");
  });

  it("should display patient email in summary", () => {
    cy.mount(
      <SuccessModal
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
        patientName={MOCK_PATIENT_NAME}
        patientEmail={MOCK_PATIENT_EMAIL}
        patientPhone={MOCK_PATIENT_PHONE}
        onClose={() => {}}
      />,
    );
    cy.contains("sarah@example.com").should("be.visible");
  });

  it("should display patient phone in summary", () => {
    cy.mount(
      <SuccessModal
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
        patientName={MOCK_PATIENT_NAME}
        patientEmail={MOCK_PATIENT_EMAIL}
        patientPhone={MOCK_PATIENT_PHONE}
        onClose={() => {}}
      />,
    );
    cy.contains("5551234567").should("be.visible");
  });

  it("should display booking ID when provided", () => {
    cy.mount(
      <SuccessModal
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
        bookingId="BK-12345"
        patientName={MOCK_PATIENT_NAME}
        patientEmail={MOCK_PATIENT_EMAIL}
        patientPhone={MOCK_PATIENT_PHONE}
        onClose={() => {}}
      />,
    );
    cy.contains("BK-12345").should("be.visible");
  });

  it("should NOT render a Done button", () => {
    cy.mount(
      <SuccessModal
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
        patientName={MOCK_PATIENT_NAME}
        patientEmail={MOCK_PATIENT_EMAIL}
        patientPhone={MOCK_PATIENT_PHONE}
        onClose={() => {}}
      />,
    );
    cy.contains("Done").should("not.exist");
  });

  it("should render 'Change date or time' link", () => {
    cy.mount(
      <SuccessModal
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
        patientName={MOCK_PATIENT_NAME}
        patientEmail={MOCK_PATIENT_EMAIL}
        patientPhone={MOCK_PATIENT_PHONE}
        onClose={() => {}}
        onChangeDateTime={cy.stub().as("changeDateTime")}
      />,
    );
    cy.contains("Change date or time").should("be.visible");
  });

  it("should fire onChangeDateTime when 'Change date or time' is clicked", () => {
    const callback = cy.stub().as("changeDateTime");
    cy.mount(
      <SuccessModal
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
        patientName={MOCK_PATIENT_NAME}
        patientEmail={MOCK_PATIENT_EMAIL}
        patientPhone={MOCK_PATIENT_PHONE}
        onClose={() => {}}
        onChangeDateTime={callback}
      />,
    );
    cy.contains("Change date or time").click();
    cy.get("@changeDateTime").should("have.been.called");
  });

  it("should auto-close after 3 seconds", () => {
    const callback = cy.stub().as("closeCallback");
    cy.mount(
      <SuccessModal
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
        patientName={MOCK_PATIENT_NAME}
        patientEmail={MOCK_PATIENT_EMAIL}
        patientPhone={MOCK_PATIENT_PHONE}
        onClose={callback}
      />,
    );
    cy.tick(3000);
    cy.get("@closeCallback").should("have.been.called");
  });

  it("should render Appointment Summary section header", () => {
    cy.mount(
      <SuccessModal
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
        patientName={MOCK_PATIENT_NAME}
        patientEmail={MOCK_PATIENT_EMAIL}
        patientPhone={MOCK_PATIENT_PHONE}
        onClose={() => {}}
      />,
    );
    cy.contains("Appointment Summary").should("be.visible");
  });

  it("should render with visual snapshot", () => {
    cy.mount(
      <SuccessModal
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
        patientName={MOCK_PATIENT_NAME}
        patientEmail={MOCK_PATIENT_EMAIL}
        patientPhone={MOCK_PATIENT_PHONE}
        onClose={() => {}}
      />,
    );
    cy.compareSnapshot({ name: "success-modal-default", testThreshold: 0.05 });
  });

  it("should render with visual snapshot - with booking ID", () => {
    cy.mount(
      <SuccessModal
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
        bookingId="BK-2026-001"
        patientName={MOCK_PATIENT_NAME}
        patientEmail={MOCK_PATIENT_EMAIL}
        patientPhone={MOCK_PATIENT_PHONE}
        onClose={() => {}}
      />,
    );
    cy.compareSnapshot({
      name: "success-modal-with-booking-id",
      testThreshold: 0.05,
    });
  });
});
