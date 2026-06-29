import { Given, When, Then } from "@badeball/cypress-cucumber-preprocessor";

Given("I am on the landing page", () => {
  cy.visit("/");
});

Given("I am on the IOPHA homepage", () => {
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
  "I should see a summary mentioning {string} and {string}",
  (keyword1: string, keyword2: string) => {
    cy.contains(keyword1).scrollIntoView().should("be.visible");
    cy.contains(keyword2).scrollIntoView().should("be.visible");
  },
);

Then(
  "I should see a physician card for {string} with {string} distance",
  (doctorName: string, distance: string) => {
    cy.contains(doctorName).should("be.visible");
    cy.contains(distance).should("be.visible");
  },
);

Then(
  "each physician card should have a {string} button",
  (buttonText: string) => {
    cy.get('button[aria-label*="Book appointment"]').should(
      "have.length.at.least",
      2,
    );
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
