import { Given, When, Then } from "@badeball/cypress-cucumber-preprocessor";

Given("I am on the landing page", () => {
  cy.visit("/");
});

When("I view the page", () => {
  cy.contains("Health Assistant").should("be.visible");
});

Then("I should see the title {string}", (expectedTitle: string) => {
  cy.contains(expectedTitle).should("be.visible");
});
