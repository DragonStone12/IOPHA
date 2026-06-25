import "./commands";

beforeEach(() => {
  cy.mockApi({
    apiPath: "/api/",
    mocksFolder: "mocks",
    cache: true,
  });
});

after(() => {
  cy.task("generateReport");
});
