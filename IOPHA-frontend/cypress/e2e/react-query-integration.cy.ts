describe("React Query Integration", () => {
  it("should fetch and display user data via React Query", () => {
    cy.visit("/");
    cy.get('[data-testid="user-name"]')
      .should("be.visible")
      .should("contain", "Test User");
    cy.get('[data-testid="user-email"]').should("contain", "test@example.com");
    cy.get('[data-testid="user-role"]').should("contain", "patient");
  });
});
