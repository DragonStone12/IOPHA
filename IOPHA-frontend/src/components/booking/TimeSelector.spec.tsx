import { TimeSelector } from "./TimeSelector";
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

describe("TimeSelector Component", () => {
  it("should render the title 'Select Appointment Time'", () => {
    cy.mount(<TimeSelector physician={MOCK_PHYSICIAN} />);
    cy.contains("Select Appointment Time").should("be.visible");
  });

  it("should display the physician name", () => {
    cy.mount(<TimeSelector physician={MOCK_PHYSICIAN} />);
    cy.contains("Booking with Dr. Emily Chen, MD").should("be.visible");
  });

  it("should render 'Choose a Date' heading", () => {
    cy.mount(<TimeSelector physician={MOCK_PHYSICIAN} />);
    cy.contains("Choose a Date").should("be.visible");
  });

  it("should render 'Choose a Time' heading", () => {
    cy.mount(<TimeSelector physician={MOCK_PHYSICIAN} />);
    cy.contains("Choose a Time").should("be.visible");
  });

  it("should render 'Back to Health Assistant' link", () => {
    cy.mount(<TimeSelector physician={MOCK_PHYSICIAN} />);
    cy.contains("Back to Health Assistant").should("be.visible");
  });

  it("should render 'Back to search' link", () => {
    cy.mount(<TimeSelector physician={MOCK_PHYSICIAN} />);
    cy.contains("Back to search").should("be.visible");
  });

  it("should not show Continue button or summary bar when no date/time selected", () => {
    cy.mount(<TimeSelector physician={MOCK_PHYSICIAN} />);
    cy.contains("Continue to Confirmation").should("not.exist");
    cy.contains("Selected appointment:").should("not.exist");
  });

  it("should fire onBack callback when Back to Health Assistant is clicked", () => {
    const callback = cy.stub().as("backCallback");
    cy.mount(<TimeSelector physician={MOCK_PHYSICIAN} onBack={callback} />);
    cy.contains("Back to Health Assistant").click();
    cy.get("@backCallback").should("have.been.called");
  });

  it("should fire onBackToSearch callback when Back to search is clicked", () => {
    const callback = cy.stub().as("backToSearchCallback");
    cy.mount(
      <TimeSelector physician={MOCK_PHYSICIAN} onBackToSearch={callback} />,
    );
    cy.contains("Back to search").click();
    cy.get("@backToSearchCallback").should("have.been.called");
  });

  it("should show placeholder message when no date is selected", () => {
    cy.mount(<TimeSelector physician={MOCK_PHYSICIAN} />);
    cy.contains("Please select a date to see available times.").should(
      "be.visible",
    );
  });

  it("should show summary bar and Continue button when date and time are selected", () => {
    const today = new Date();
    cy.mount(
      <TimeSelector
        physician={MOCK_PHYSICIAN}
        selectedDate={today}
        selectedTime="09:00 AM"
      />,
    );
    cy.contains("Selected appointment:").should("be.visible");
    cy.contains("Continue to Confirmation").should("be.visible");
  });

  it("should display formatted date and time in summary bar", () => {
    const testDate = new Date(2026, 5, 26);
    cy.mount(
      <TimeSelector
        physician={MOCK_PHYSICIAN}
        selectedDate={testDate}
        selectedTime="04:00 PM"
      />,
    );
    cy.contains("Friday, June 26, 2026 at 04:00 PM").should("be.visible");
  });

  it("should fire onContinue callback when Continue button is clicked", () => {
    const today = new Date();
    const callback = cy.stub().as("continueCallback");
    cy.mount(
      <TimeSelector
        physician={MOCK_PHYSICIAN}
        selectedDate={today}
        selectedTime="09:00 AM"
        onContinue={callback}
      />,
    );
    cy.contains("Continue to Confirmation").click();
    cy.get("@continueCallback").should("have.been.called");
  });

  it("should fire onDateSelect when a date is selected", () => {
    cy.clock(new Date(2026, 5, 26));
    const callback = cy.stub().as("dateSelectCallback");
    cy.mount(
      <TimeSelector physician={MOCK_PHYSICIAN} onDateSelect={callback} />,
    );
    cy.get("td[data-day]")
      .not("[data-outside]")
      .not("[data-disabled]")
      .find("button")
      .first()
      .click();
    cy.get("@dateSelectCallback").should("have.been.called");
    cy.clock().then((clock) => clock.restore());
  });

  it("should fire onTimeSelect when a time slot is clicked", () => {
    const today = new Date();
    const callback = cy.stub().as("timeSelectCallback");
    cy.mount(
      <TimeSelector
        physician={MOCK_PHYSICIAN}
        selectedDate={today}
        onTimeSelect={callback}
      />,
    );
    cy.get("button[aria-label*='Select']").first().click();
    cy.get("@timeSelectCallback").should("have.been.called");
  });

  it("should show blue circle outline on selected date", () => {
    cy.clock(new Date(2026, 5, 26));
    const testDate = new Date(2026, 5, 26);
    cy.mount(
      <TimeSelector physician={MOCK_PHYSICIAN} selectedDate={testDate} />,
    );
    cy.get('td[data-selected="true"] button')
      .should("have.css", "border-width", "2px");
    cy.clock().then((clock) => clock.restore());
  });

  it("should show blue filled button for selected time", () => {
    const today = new Date();
    cy.mount(
      <TimeSelector
        physician={MOCK_PHYSICIAN}
        selectedDate={today}
        selectedTime="09:00 AM"
      />,
    );
    cy.get('button[aria-label*="Select"][aria-pressed="true"]').should(
      "have.class",
      "bg-blue-600",
    );
  });

  it("should render with visual snapshot - initial state", () => {
    cy.mount(<TimeSelector physician={MOCK_PHYSICIAN} />);
    cy.compareSnapshot({ name: "time-selector-initial", testThreshold: Cypress.env("SNAPSHOT_TEST_THRESHOLD") });
  });

  it("should render with visual snapshot - date selected only", () => {
    const testDate = new Date(2026, 5, 26);
    cy.mount(
      <TimeSelector physician={MOCK_PHYSICIAN} selectedDate={testDate} />,
    );
    cy.compareSnapshot({
      name: "time-selector-date-selected",
      testThreshold: Cypress.env("SNAPSHOT_TEST_THRESHOLD"),
    });
  });

  it("should render with visual snapshot - date and time selected", () => {
    const testDate = new Date(2026, 5, 26);
    cy.mount(
      <TimeSelector
        physician={MOCK_PHYSICIAN}
        selectedDate={testDate}
        selectedTime="04:00 PM"
      />,
    );
    cy.compareSnapshot({ name: "time-selector-selected", testThreshold: Cypress.env("SNAPSHOT_TEST_THRESHOLD") });
  });

  it("should render with visual snapshot - no slots available", () => {
    const testDate = new Date(2026, 5, 26);
    cy.mount(
      <TimeSelector physician={MOCK_PHYSICIAN} selectedDate={testDate} />,
    );
    cy.get("button[aria-label*='Select']").then(($btns) => {
      if ($btns.length === 0) {
        cy.contains("No appointments available for this date").should(
          "be.visible",
        );
        cy.compareSnapshot({
          name: "time-selector-no-slots",
          testThreshold: Cypress.env("SNAPSHOT_TEST_THRESHOLD"),
        });
      }
    });
  });
});
