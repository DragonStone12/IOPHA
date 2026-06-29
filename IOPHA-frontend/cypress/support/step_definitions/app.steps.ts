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
