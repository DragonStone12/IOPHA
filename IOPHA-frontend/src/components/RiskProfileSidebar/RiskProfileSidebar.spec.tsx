import { RiskProfileSidebar } from "./RiskProfileSidebar";

describe("RiskProfileSidebar Component", () => {
  it("should render user card with correct details", () => {
    cy.mount(
      <RiskProfileSidebar
        userName="Test User"
        userAge={28}
        userLocation="New York, NY"
      />,
    );
    cy.contains("Test User").should("be.visible");
    cy.contains("28 years").should("be.visible");
    cy.contains("New York, NY").should("be.visible");
  });

  it("should render initials in avatar when no image provided", () => {
    cy.mount(<RiskProfileSidebar userName="John Doe" />);
    cy.contains("JD").should("be.visible");
  });

  it("should render risk score bar with correct width", () => {
    cy.mount(<RiskProfileSidebar riskScore={78} />);
    cy.get('[data-slot="progress-indicator"]').should("have.css", "width");
  });

  it("should display HIGH RISK badge when score > 70", () => {
    cy.mount(<RiskProfileSidebar riskScore={85} />);
    cy.contains("HIGH RISK").should("be.visible");
  });

  it("should display MODERATE RISK badge when score is 40-70", () => {
    cy.mount(<RiskProfileSidebar riskScore={55} />);
    cy.contains("MODERATE RISK").should("be.visible");
  });

  it("should display LOW RISK badge when score < 40", () => {
    cy.mount(<RiskProfileSidebar riskScore={20} />);
    cy.contains("LOW RISK").should("be.visible");
  });

  it("should render all contributing factors", () => {
    cy.mount(
      <RiskProfileSidebar
        contributingFactors={["Factor 1", "Factor 2", "Factor 3"]}
      />,
    );
    cy.contains("Factor 1").should("be.visible");
    cy.contains("Factor 2").should("be.visible");
    cy.contains("Factor 3").should("be.visible");
  });

  it("should render Quick Start navigation items", () => {
    cy.mount(<RiskProfileSidebar />);
    cy.contains("Weight & nutrition tips").should("be.visible");
    cy.contains("Find a doctor").should("be.visible");
    cy.contains("Exercise guidance").should("be.visible");
    cy.contains("Sleep & recovery").should("be.visible");
  });

  it("should render BMI and last assessed info", () => {
    cy.mount(<RiskProfileSidebar bmi={28.5} lastAssessed="yesterday" />);
    cy.contains("BMI 28.5").should("be.visible");
    cy.contains("Last assessed yesterday").should("be.visible");
  });
});
