describe("Visual Regression Tests", () => {
  it("should compare the landing page", () => {
    cy.visit("/");
    cy.compareSnapshot("landing-page");
  });
});