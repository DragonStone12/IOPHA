class AppPage {
  visit() {
    cy.visit('/');
    return this;
  }

  getTitle() {
    return cy.get('h1');
  }

  verifyTitle(expectedTitle: string) {
    this.getTitle().should('contain', expectedTitle);
    return this;
  }

  verifyPageLoaded() {
    this.getTitle().should('be.visible');
    return this;
  }
}

const app = new AppPage();
export default app;