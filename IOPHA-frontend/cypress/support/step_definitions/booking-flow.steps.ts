import { Given, When, Then } from "@badeball/cypress-cucumber-preprocessor";

When(
  "I click the {string} button on a physician card",
  (buttonText: string) => {
    cy.get("main").contains(buttonText).click();
  },
);

When("I click on {string} physician name", (doctorName: string) => {
  cy.contains(doctorName).click();
});

Then("I should see the {string} screen", (screenTitle: string) => {
  cy.contains(screenTitle).should("be.visible");
});

Then("I should see {string} heading", (heading: string) => {
  cy.contains(heading).should("be.visible");
});

Then("I should see {string} button", (buttonText: string) => {
  cy.contains(buttonText).should("be.visible");
});

Then("I should see {string} link", (linkText: string) => {
  cy.contains(linkText).should("be.visible");
});

When("I select a date on the calendar", () => {
  cy.get("td[data-day]")
    .not("[data-outside]")
    .not("[data-disabled]")
    .find("button")
    .first()
    .click();
});

When("I select a time slot", () => {
  cy.get("button[aria-label*='Select']").first().click();
});

Then("I should see time slots available", () => {
  cy.get("button[aria-label*='Select']").should("have.length.at.least", 1);
});

Then("I should see the summary bar", () => {
  cy.contains("Selected appointment:").should("be.visible");
});

Then("I should see {string} text", (text: string) => {
  cy.contains(text).should("be.visible");
});

Then("I should not see the summary bar", () => {
  cy.contains("Selected appointment:").should("not.exist");
});

When("I click the {string} button", (buttonText: string) => {
  cy.contains(buttonText).click();
});

When("I fill in the patient name field with {string}", (value: string) => {
  cy.get("#patient-name").type(value);
});

When("I fill in the patient email field with {string}", (value: string) => {
  cy.get("#patient-email").type(value);
});

When("I fill in the patient phone field with {string}", (value: string) => {
  cy.get("#patient-phone").type(value);
});

When(
  "I click the {string} button without filling fields",
  (buttonText: string) => {
    cy.contains(buttonText).click();
  },
);

Then("I should see validation errors for required fields", () => {
  cy.contains("This field is required").should("be.visible");
});

When("I click the {string} link", (linkText: string) => {
  cy.contains(linkText).click();
});

Then("I should see the chat interface", () => {
  cy.contains("Health Assistant").should("be.visible");
  cy.get('input[placeholder*="Ask about nutrition"]').should("be.visible");
});

Then("I should see the time selector initial state", () => {
  cy.get("main").compareSnapshot("booking-time-selector-initial");
});

Then("I should see the time selector with selection state", () => {
  cy.get("main").compareSnapshot("booking-time-selector-selected");
});

Then("I should see the confirmation form default state", () => {
  cy.get("main").compareSnapshot("booking-confirmation-form-default");
});

Then("I should see the appointment confirmation state", () => {
  cy.get("main").compareSnapshot("booking-appointment-confirmation");
});

Then("I should see the appointment confirmation box in chat", () => {
  cy.contains("Appointment confirmed").should("be.visible");
  cy.contains("Weight & nutrition tips").should("be.visible");
  cy.contains("Exercise guidance").should("be.visible");
  cy.contains("Sleep & recovery").should("be.visible");
});

Then("I should see {string} field validation error", (fieldName: string) => {
  cy.contains(fieldName).should("be.visible");
});

Then("I should see the confirmation form with validation errors", () => {
  cy.get("main").compareSnapshot("booking-confirmation-form-errors");
});

Then("I should not see the name validation error", () => {
  cy.get("#patient-name").parent().find('p[role="alert"]').should("not.exist");
});

Then("I should see the corrected form state", () => {
  cy.get("main").compareSnapshot("booking-confirmation-form-corrected");
});

Then("I should not see a {string} button", (buttonText: string) => {
  cy.contains(buttonText).should("not.exist");
});

When("I wait for {int} seconds", (seconds: number) => {
  cy.wait(seconds * 1000);
});
