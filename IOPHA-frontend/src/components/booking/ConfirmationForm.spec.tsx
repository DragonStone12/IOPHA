import { ConfirmationForm } from "./ConfirmationForm";
import type { Physician } from "../NutritionResponse/PhysicianCard";

const MOCK_PHYSICIAN: Physician = {
  id: "dr-chen",
  name: "Dr. Emily Chen, MD",
  specialty: "Obesity & Metabolic Medicine",
  distance: "1.8 miles",
  rating: 4.9,
  reviewCount: 234,
  nextAvailable: "Today, 3:30 PM",
  imageUrl:
    "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=200&h=200&fit=crop&auto=format",
};

const MOCK_DATE = new Date(2026, 5, 26);
const MOCK_TIME = "04:00 PM";

describe("ConfirmationForm Component", () => {
  it("should render the title 'Confirm Your Appointment'", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.contains("Confirm Your Appointment").should("be.visible");
  });

  it("should render correct subtitle", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.contains(
      "Please review your appointment details and provide your information",
    ).should("be.visible");
  });

  it("should render 'Patient Information' heading", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.contains("Patient Information").should("be.visible");
  });

  it("should render 'Appointment Details' heading", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.contains("Appointment Details").should("be.visible");
  });

  it("should display physician name in details", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.contains("Dr. Emily Chen, MD").should("be.visible");
  });

  it("should display physician specialty in details", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.contains("Obesity & Metabolic Medicine").should("be.visible");
  });

  it("should display selected date in details", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.contains("Friday, June 26, 2026").should("be.visible");
  });

  it("should display selected time in details", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.contains("04:00 PM").should("be.visible");
  });

  it("should display location in details", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.contains("Baylor University Medical Center").should("be.visible");
  });

  it("should render Full Name input field", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.get('label[for="patient-name"]').should("be.visible");
    cy.get("#patient-name").should("be.visible");
  });

  it("should render Email Address input field", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.get('label[for="patient-email"]').should("be.visible");
    cy.get("#patient-email").should("be.visible");
  });

  it("should render Phone Number input field", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.get('label[for="patient-phone"]').should("be.visible");
    cy.get("#patient-phone").should("be.visible");
  });

  it("should render Reason for Visit textarea", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.get('label[for="patient-reason"]').should("be.visible");
    cy.get("#patient-reason").should("be.visible");
  });

  it("should render Confirm Appointment button inside the form card", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.contains("Confirm Appointment").should("be.visible");
  });

  it("should render 'Change date or time' link", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.contains("Change date or time").should("be.visible");
  });

  it("should render 'Back to calendar' link", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.contains("Back to calendar").should("be.visible");
  });

  it("should render note box with arrival instructions", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.contains("Please arrive 15 minutes early").should("be.visible");
  });

  it("should fire onChangeDateTime callback when Change date or time is clicked", () => {
    const callback = cy.stub().as("changeDateTimeCallback");
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
        onChangeDateTime={callback}
      />,
    );
    cy.contains("Change date or time").click();
    cy.get("@changeDateTimeCallback").should("have.been.called");
  });

  it("should fire onBack callback when Back to calendar is clicked", () => {
    const callback = cy.stub().as("backCallback");
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
        onBack={callback}
      />,
    );
    cy.contains("Back to calendar").click();
    cy.get("@backCallback").should("have.been.called");
  });

  it("should show validation error on blur - name field", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.get("#patient-name").focus().blur();
    cy.contains("This field is required").should("be.visible");
  });

  it("should show validation error on blur - email field", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.get("#patient-email").focus().blur();
    cy.contains("This field is required").should("be.visible");
  });

  it("should show validation error on blur - phone field", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.get("#patient-phone").focus().blur();
    cy.contains("This field is required").should("be.visible");
  });

  it("should clear error when user corrects the field", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.get("#patient-name").focus().blur();
    cy.contains("This field is required").should("be.visible");
    cy.get("#patient-name").type("John Doe");
    cy.contains("This field is required").should("not.exist");
  });

  it("should clear email error when user enters valid email", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.get("#patient-email").type("invalid").blur();
    cy.contains("Please enter a valid email address").should("be.visible");
    cy.get("#patient-email").clear().type("john@example.com");
    cy.contains("Please enter a valid email address").should("not.exist");
  });

  it("should clear phone error when user enters valid phone", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.get("#patient-phone").type("abc").blur();
    cy.contains("Please enter a valid 10-digit phone number").should(
      "be.visible",
    );
    cy.get("#patient-phone").clear().type("1234567890");
    cy.contains("Please enter a valid 10-digit phone number").should(
      "not.exist",
    );
  });

  it("should show error-then-correct transition with snapshot", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    // Trigger errors on all fields
    cy.get("#patient-name").focus().blur();
    cy.get("#patient-email").focus().blur();
    cy.get("#patient-phone").focus().blur();
    cy.contains("This field is required").should("be.visible");
    cy.compareSnapshot({
      name: "confirmation-form-errors-on-blur",
      testThreshold: 0.05,
    });

    // Correct all fields
    cy.get("#patient-name").type("John Doe");
    cy.get("#patient-email").type("john@example.com");
    cy.get("#patient-phone").type("1234567890");
    cy.contains("This field is required").should("not.exist");
    cy.compareSnapshot("confirmation-form-corrected-from-errors");
  });

  it("should show validation errors on submit with snapshot", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.contains("Confirm Appointment").click();
    cy.contains("This field is required").should("be.visible");
    cy.compareSnapshot("confirmation-form-errors-on-submit");
  });

  it("should show corrected form state with snapshot", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.get("#patient-name").focus().blur();
    cy.get("#patient-name").type("John Doe");
    cy.get("#patient-email").type("john@example.com");
    cy.get("#patient-phone").type("1234567890");
    cy.compareSnapshot("confirmation-form-corrected-from-errors");
  });

  it("should fire onConfirm callback with valid data including reason", () => {
    const callback = cy.stub().as("confirmCallback");
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
        onConfirm={callback}
      />,
    );
    cy.get("#patient-name").type("John Doe");
    cy.get("#patient-email").type("john@example.com");
    cy.get("#patient-phone").type("1234567890");
    cy.get("#patient-reason").type("Annual checkup");
    cy.contains("Confirm Appointment").click();
    cy.get("@confirmCallback").should("have.been.calledWith", {
      name: "John Doe",
      email: "john@example.com",
      phone: "1234567890",
      reason: "Annual checkup",
    });
  });

  it("should fire onConfirm callback with valid data without reason", () => {
    const callback = cy.stub().as("confirmCallback");
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
        onConfirm={callback}
      />,
    );
    cy.get("#patient-name").type("John Doe");
    cy.get("#patient-email").type("john@example.com");
    cy.get("#patient-phone").type("1234567890");
    cy.contains("Confirm Appointment").click();
    cy.get("@confirmCallback").should("have.been.calledWith", {
      name: "John Doe",
      email: "john@example.com",
      phone: "1234567890",
      reason: "",
    });
  });

  it("should pre-fill patient data when provided", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
        patientName="Sarah Mitchell"
        patientEmail="sarah@example.com"
        patientPhone="5551234567"
      />,
    );
    cy.get("#patient-name").should("have.value", "Sarah Mitchell");
    cy.get("#patient-email").should("have.value", "sarah@example.com");
    cy.get("#patient-phone").should("have.value", "5551234567");
  });

  it("should strip non-digit characters from phone input", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.get("#patient-phone").type("abc123def456");
    cy.get("#patient-phone").should("have.value", "123456");
  });

  it("should render with visual snapshot - default state", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
        patientName="Sarah Mitchell"
        patientEmail="sarah@example.com"
        patientPhone="5551234567"
      />,
    );
    cy.compareSnapshot("confirmation-form-default");
  });

  it("should render with visual snapshot - empty form", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.compareSnapshot("confirmation-form-empty");
  });

  it("should render with visual snapshot - validation errors", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.contains("Confirm Appointment").click();
    cy.compareSnapshot("confirmation-form-validation-errors");
  });

  it("should render with visual snapshot - partial fill with email error", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
      />,
    );
    cy.get("#patient-name").type("John Doe");
    cy.get("#patient-email").type("invalid-email");
    cy.get("#patient-phone").type("1234567890");
    cy.contains("Confirm Appointment").click();
    cy.compareSnapshot("confirmation-form-email-error");
  });

  it("should render with visual snapshot - fully filled form", () => {
    cy.mount(
      <ConfirmationForm
        physician={MOCK_PHYSICIAN}
        selectedDate={MOCK_DATE}
        selectedTime={MOCK_TIME}
        onConfirm={() => {}}
      />,
    );
    cy.get("#patient-name").type("John Doe");
    cy.get("#patient-email").type("john@example.com");
    cy.get("#patient-phone").type("1234567890");
    cy.get("#patient-reason").type("Annual checkup");
    cy.compareSnapshot("confirmation-form-filled");
  });
});
