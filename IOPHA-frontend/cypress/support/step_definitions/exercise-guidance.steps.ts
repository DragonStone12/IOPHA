import { Then } from "@badeball/cypress-cucumber-preprocessor";

Then(
  "I should see {int} numbered exercise recommendation cards",
  (count: number) => {
    cy.get("[aria-posinset]").should("have.length", count);
  },
);
