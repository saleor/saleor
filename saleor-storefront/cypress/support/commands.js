/// <reference types="cypress" />
import "./login";

Cypress.Commands.add("visitStubbed", (url, operations = {}) => {
  function responseStub(result) {
    return {
      json() {
        return Promise.resolve(result);
      },
      text() {
        return Promise.resolve(JSON.stringify(result));
      },
      ok: true
    };
  }

  function serverStub(path, req) {
    const body = JSON.parse(req.body);
    const { operationName } = body[0];

    if (Object.keys(operations).indexOf(operationName) !== false) {
      return Promise.resolve(responseStub(operations[operationName]));
    }

    return Promise.reject(new Error(`Not found: ${path}`));
  }

  cy.visit(url, {
    onBeforeLoad: win => {
      cy.stub(win, "fetch")
        .callsFake(serverStub)
        .as("fetch stub");
    }
  });
});

Cypress.Commands.add("mockGraphQL", stubs => {
  cy.on("window:before:load", win => {
    cy.stub(win, "fetch", (...args) => {
      const [url, request] = args;
      const postBody = JSON.parse(request.body)[0];
      let promise;

      if (url.indexOf("graphql") !== -1) {
        stubs.some(stub => {
          if (postBody.operationName === stub.operation) {
            promise = Promise.resolve({
              ok: true,
              text() {
                return Promise.resolve(JSON.stringify(stub.response));
              }
            });
            return true;
          }
        });
      }

      if (promise) {
        return promise;
      }

      console.log("Could not find a stub for the operation.");
      return false;
    });
  });
});

Cypress.on("uncaught:exception", () => {
  return false;
});

Cypress.Commands.add("setup", polyfill => {
  cy.visit("/", {
    onBeforeLoad(win) {
      delete win.fetch;
      win.eval(polyfill);
      win.fetch = win.unfetch;
    }
  });
});
