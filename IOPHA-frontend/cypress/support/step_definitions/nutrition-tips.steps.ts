import { Then } from "@badeball/cypress-cucumber-preprocessor";

Then(
  "I should see the introductory text mentioning {string}",
  (keyword: string) => {
    cy.contains(keyword).should("be.visible");
  },
);

Then("I should see 3 numbered dietary adjustment cards", () => {
  cy.get("[aria-posinset]").should("have.length", 3);
  cy.get('[aria-posinset="1"]').should("be.visible");
  cy.get('[aria-posinset="2"]').should("be.visible");
  cy.get('[aria-posinset="3"]').should("be.visible");
});

Then("I should see a physician card for {string}", (doctorName: string) => {
  cy.contains(doctorName).should("be.visible");
});

Then(
  "I should see a {string} button on the physician card",
  (buttonText: string) => {
    cy.contains(buttonText).should("be.visible");
  },
);

Then(
  "I should see follow-up chips including {string} and {string}",
  (chip1: string, chip2: string) => {
    cy.contains(chip1).should("be.visible");
    cy.contains(chip2).should("be.visible");
  },
);
