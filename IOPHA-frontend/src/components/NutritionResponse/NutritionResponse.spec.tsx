import { NutritionResponse } from "./NutritionResponse";
import type { NutritionResponseData, Physician } from "./NutritionResponse";

const MOCK_PHYSICIAN: Physician = {
  id: "dr-chen",
  name: "Dr. Emily Chen, MD",
  specialty: "Obesity & Metabolic Medicine",
  distance: "1.8 miles",
  rating: 4.9,
  reviewCount: 234,
  nextAvailable: "Today, 3:30 PM",
};

const MOCK_DATA: NutritionResponseData = {
  introText:
    "Based on your profile and current clinical guidelines, here are three evidence-based dietary adjustments most effective for your risk factors. Because your assessment noted irregular meal timing, aligning your eating window with your waking hours is particularly impactful.",
  tips: [
    {
      number: 1,
      title: "Time-restricted eating — 10-hour window",
      description:
        "Limit food intake to a consistent window such as 8 AM–6 PM. This alone reduces average daily caloric intake by 15–20% without strict counting and improves insulin sensitivity within 2 weeks.",
    },
    {
      number: 2,
      title: "Protein-first meals",
      description:
        "Begin each meal with 25–30g of lean protein (eggs, chicken, legumes). This slows gastric emptying, regulates appetite hormones, and reduces overall meal calories without hunger.",
    },
    {
      number: 3,
      title: "Eliminate liquid calories",
      description:
        "Replacing sweetened beverages with water, black coffee, or unsweetened tea removes an average of 350 excess calories per day — one of the highest-return single changes for your profile.",
    },
  ],
  physician: MOCK_PHYSICIAN,
  followUpChips: [
    "Exercise tips",
    "Book Dr. Chen",
    "Sleep advice",
    "More nutrition guidance",
  ],
};

describe("NutritionResponse Component", () => {
  it("should render the introductory text mentioning irregular meal timing", () => {
    cy.mount(<NutritionResponse data={MOCK_DATA} />);
    cy.contains("irregular meal timing").should("be.visible");
    cy.compareSnapshot({
      name: "nutrition-response-default",
      testThreshold: Cypress.env("SNAPSHOT_TEST_THRESHOLD"),
    });
  });

  it("should render exactly 3 numbered dietary adjustment cards", () => {
    cy.mount(<NutritionResponse data={MOCK_DATA} />);
    cy.get("[aria-posinset]").should("have.length", 3);
    cy.contains("Time-restricted eating").should("be.visible");
    cy.contains("Protein-first meals").should("be.visible");
    cy.contains("Eliminate liquid calories").should("be.visible");
  });

  it("should render tip descriptions", () => {
    cy.mount(<NutritionResponse data={MOCK_DATA} />);
    cy.contains("15–20%").should("be.visible");
    cy.contains("25–30g of lean protein").should("be.visible");
    cy.contains("350 excess calories").should("be.visible");
  });

  it("should render a physician card for Dr. Emily Chen", () => {
    cy.mount(<NutritionResponse data={MOCK_DATA} />);
    cy.contains("Dr. Emily Chen, MD").should("be.visible");
    cy.contains("Obesity & Metabolic Medicine").should("be.visible");
  });

  it("should render physician metadata (distance, rating, availability)", () => {
    cy.mount(<NutritionResponse data={MOCK_DATA} />);
    cy.contains("1.8 miles").should("be.visible");
    cy.contains("4.9 (234)").should("be.visible");
    cy.contains("Today, 3:30 PM").should("be.visible");
  });

  it("should render a Book button on the physician card", () => {
    cy.mount(<NutritionResponse data={MOCK_DATA} />);
    cy.contains("Book").should("be.visible");
  });

  it("should render follow-up chips including Exercise tips and Book Dr. Chen", () => {
    cy.mount(<NutritionResponse data={MOCK_DATA} />);
    cy.contains("Exercise tips").should("be.visible");
    cy.contains("Book Dr. Chen").should("be.visible");
    cy.contains("Sleep advice").should("be.visible");
    cy.contains("More nutrition guidance").should("be.visible");
  });

  it("should fire onChipSelect callback when a follow-up chip is clicked", () => {
    const callback = cy.stub().as("chipSelect");
    cy.mount(<NutritionResponse data={MOCK_DATA} onChipSelect={callback} />);
    cy.contains("Exercise tips").click();
    cy.get("@chipSelect").should("have.been.calledWith", "Exercise tips");
  });

  it("should fire onBookPhysician callback when Book button is clicked", () => {
    const callback = cy.stub().as("bookPhysician");
    cy.mount(<NutritionResponse data={MOCK_DATA} onBookPhysician={callback} />);
    cy.contains("Book").click();
    cy.get("@bookPhysician").should("have.been.called");
  });

  it("should render without physician card when physician is omitted", () => {
    const dataWithoutPhysician: NutritionResponseData = {
      ...MOCK_DATA,
      physician: undefined,
    };
    cy.mount(<NutritionResponse data={dataWithoutPhysician} />);
    cy.contains("Nearby Baylor Physicians").should("not.exist");
    cy.contains("Dr. Emily Chen, MD").should("not.exist");
  });

  it("should display numbered badges 1, 2, 3 for tip cards", () => {
    cy.mount(<NutritionResponse data={MOCK_DATA} />);
    cy.get('[aria-posinset="1"]').should("exist");
    cy.get('[aria-posinset="2"]').should("exist");
    cy.get('[aria-posinset="3"]').should("exist");
  });

  it("should render the Nearby Baylor Physicians section header", () => {
    cy.mount(<NutritionResponse data={MOCK_DATA} />);
    cy.contains("Nearby Baylor Physicians").should("be.visible");
  });
});
