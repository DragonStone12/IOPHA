import { Then } from "@badeball/cypress-cucumber-preprocessor";

Then(
  "I should see introductory text mentioning {string} and {string}",
  (keyword1: string, keyword2: string) => {
    cy.contains(keyword1).scrollIntoView().should("be.visible");
    cy.contains(keyword2).scrollIntoView().should("be.visible");
  },
);

Then(
  "I should see {int} numbered exercise recommendation cards",
  (count: number) => {
    cy.get("[aria-posinset]").should("have.length", count);
  },
);

Then("the first card should be titled {string}", (title: string) => {
  cy.get('[aria-posinset="1"]').contains(title).should("be.visible");
});

Then("the second card should be titled {string}", (title: string) => {
  cy.get('[aria-posinset="2"]').contains(title).should("be.visible");
});

Then("the third card should be titled {string}", (title: string) => {
  cy.get('[aria-posinset="3"]').contains(title).should("be.visible");
});
