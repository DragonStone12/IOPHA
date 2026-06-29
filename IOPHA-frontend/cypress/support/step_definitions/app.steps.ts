import { Given, When, Then } from "@badeball/cypress-cucumber-preprocessor";

Given("I am on the IOPHA homepage", () => {
  cy.visit("/");
});

Given("I am on the landing page", () => {
  cy.visit("/");
});

When("I view the page", () => {
  cy.contains("Health Assistant").should("be.visible");
});

When("I click the {string} chip", (chipLabel: string) => {
  cy.get("main").contains(chipLabel).click();
});

Then("I should see the title {string}", (expectedTitle: string) => {
  cy.contains(expectedTitle).should("be.visible");
});

Then(
  "I should see the introductory text mentioning {string}",
  (keyword: string) => {
    cy.contains(keyword).scrollIntoView().should("be.visible");
  },
);

Then("I should see 3 numbered dietary adjustment cards", () => {
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
