import { TipCard } from "./TipCard";
import type { Tip } from "./TipCard";

const MOCK_TIP: Tip = {
  number: 1,
  title: "Time-restricted eating — 10-hour window",
  description:
    "Limit food intake to a consistent window such as 8 AM–6 PM. This alone reduces average daily caloric intake by 15–20% without strict counting and improves insulin sensitivity within 2 weeks.",
};

describe("TipCard Component", () => {
  it("should render tip number badge", () => {
    cy.mount(<TipCard tip={MOCK_TIP} />);
    cy.contains("1").should("be.visible");
  });

  it("should render tip title", () => {
    cy.mount(<TipCard tip={MOCK_TIP} />);
    cy.contains("Time-restricted eating").should("be.visible");
  });

  it("should render tip description", () => {
    cy.mount(<TipCard tip={MOCK_TIP} />);
    cy.contains("15–20%").should("be.visible");
  });

  it("should have aria-posinset attribute matching tip number", () => {
    cy.mount(<TipCard tip={MOCK_TIP} />);
    cy.get('[aria-posinset="1"]').should("exist");
  });

  it("should have aria-setsize of 3", () => {
    cy.mount(<TipCard tip={MOCK_TIP} />);
    cy.get('[aria-setsize="3"]').should("exist");
  });

  it("should apply custom className", () => {
    cy.mount(<TipCard tip={MOCK_TIP} className="custom-class" />);
    cy.get(".custom-class").should("exist");
  });

  it("should render with visual snapshot", () => {
    cy.mount(<TipCard tip={MOCK_TIP} />);
    cy.compareSnapshot({ name: "tip-card-default", testThreshold: Cypress.env("SNAPSHOT_TEST_THRESHOLD") });
  });
});
