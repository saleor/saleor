import { userBuilder } from "../generate";

const createUser = () => {
  const user = userBuilder();
  return cy
    .request({
      body: user,
      method: "POST",
      url: `${Cypress.env("BACKEND_URL")}/${Cypress.env("GRAPHQL_ID")}/`
    })
    .then(response => response.body.user);
};

Cypress.Commands.add("createUser", createUser);

const loginOrRegisterUser = (type = "login", user) => {
  const tabSelector =
    type === "login"
      ? ".login__tabs span.active-tab"
      : ".login__tabs span:not(.active-tab)";

  return cy
    .getByTestId("login-btn")
    .click()
    .get(tabSelector)
    .click()
    .get(".login__content input[name='email']")
    .type(user.email)
    .get(".login__content input[name='password']")
    .type(user.password)
    .get(".login__content button[type='submit']")
    .click();
};

Cypress.Commands.add("registerUser", user =>
  loginOrRegisterUser("register", user)
);
Cypress.Commands.add("loginUser", user => loginOrRegisterUser("login", user));
Cypress.Commands.add("logoutUser", () =>
  cy
    .getByTestId("user-btn", { timeout: 3000 })
    .trigger("mouseover")
    .getByTestId("logout-link")
    .click()
);
