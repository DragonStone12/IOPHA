import { LandingPage } from "./LandingPage";

describe("LandingPage Component", () => {
  it("should render with default props", () => {
    cy.mount(<LandingPage />);
    cy.get("h1").should("contain", "Health Assistant");
    cy.contains("Sarah Mitchell").should("be.visible");
    cy.contains("78").should("be.visible");
    cy.contains("/100").should("be.visible");
    cy.contains("Baylor Scott & White Health").should("be.visible");
    cy.compareSnapshot({
      name: "landing-page-default",
      testThreshold: Cypress.env("SNAPSHOT_TEST_THRESHOLD"),
    });
  });

  it("should render with custom props", () => {
    cy.mount(
      <LandingPage
        userName="John Doe"
        riskScore={85}
        hospitalName="Test Hospital"
      />,
    );
    cy.contains("John Doe").should("be.visible");
    cy.contains("85").should("be.visible");
    cy.contains("Test Hospital").should("be.visible");
  });

  it("should display HIGH RISK badge when score > 70", () => {
    cy.mount(<LandingPage riskScore={78} />);
    cy.contains("HIGH RISK").should("be.visible");
  });

  it("should display MODERATE RISK badge when score is 40-70", () => {
    cy.mount(<LandingPage riskScore={50} />);
    cy.contains("MODERATE RISK").should("be.visible");
  });

  it("should display LOW RISK badge when score < 40", () => {
    cy.mount(<LandingPage riskScore={25} />);
    cy.contains("LOW RISK").should("be.visible");
  });

  it("should render all 4 action chips", () => {
    cy.mount(<LandingPage />);
    cy.get("main .flex-wrap button").should("have.length", 4);
    cy.contains("Weight & nutrition tips").should("be.visible");
    cy.contains("Find a doctor").should("be.visible");
    cy.contains("Exercise guidance").should("be.visible");
    cy.contains("Sleep & recovery").should("be.visible");
  });

  it("should render greeting message with correct template", () => {
    cy.mount(<LandingPage userName="Jane Doe" riskScore={65} />);
    cy.contains("Welcome, Jane Doe").should("be.visible");
    cy.contains("65/100").should("be.visible");
  });

  it("should render contributing factors list", () => {
    cy.mount(<LandingPage />);
    cy.contains("Sedentary lifestyle").should("be.visible");
    cy.contains("High-calorie diet").should("be.visible");
    cy.contains("Family history").should("be.visible");
    cy.contains("Irregular sleep").should("be.visible");
  });

  it("should render disclaimer text", () => {
    cy.mount(<LandingPage />);
    cy.contains("AI responses are for informational purposes only").should(
      "be.visible",
    );
    cy.contains("Not a substitute for professional medical advice").should(
      "be.visible",
    );
  });
});
