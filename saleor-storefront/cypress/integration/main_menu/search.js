/// <reference types="cypress" />

describe.only("Search", () => {
  const typedText = "t";
  let polyfill;

  before(() => {
    const polyfillUrl = "https://unpkg.com/unfetch/dist/unfetch.umd.js";
    cy.request(polyfillUrl).then(response => {
      polyfill = response.body;
    });
  });

  beforeEach(() => {
    cy.server();
    cy.route(
      "POST",
      `${Cypress.env("BACKEND_URL")}/${Cypress.env("GRAPHQL_ID")}/`
    ).as("graphqlQuery");

    cy.setup(polyfill);
    cy.wait("@graphqlQuery");
    cy.get(".main-menu__search")
      .click()
      .get("form.search input")
      .as("searchInput");
  });

  it("should show input on click", () => {
    cy.get("@searchInput").should("exist");
  });

  it("should search products", () => {
    cy.get("@searchInput")
      .type(typedText)
      .get(".search__products.search__products--expanded")
      .should("exist");
  });

  it("should redirect to Search page on form submit", () => {
    cy.get("@searchInput").type(typedText);
    cy.get("form.search button[type='submit']").click();

    cy.url().should("include", `/search/?q=${typedText}`);
    cy.get(".search-page").should("exist");
    cy.focused().should("have.value", typedText);
  });
});
