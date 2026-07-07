import { mount } from "cypress/react";
import "../../src/index.css";
import "./commands";

declare global {
  namespace Cypress {
    interface Chainable {
      mount: typeof mount;
    }
  }
}

Cypress.Commands.add("mount", mount);

Cypress.on("window:before:load", (win) => {
  cy.stub(win.Math, "random").returns(0.4);
});
