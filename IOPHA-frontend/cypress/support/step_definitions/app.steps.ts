import { Given, When, Then } from "@badeball/cypress-cucumber-preprocessor";

Given("I am on the IOPHA homepage", () => {
  cy.visit("/");
});

When("I view the page", () => {
  cy.get("h1").should("be.visible");
});

Then("I should see the title {string}", (expectedTitle: string) => {
  cy.get("h1").should("contain", expectedTitle);
});
