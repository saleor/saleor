import * as Cookies from "universal-cookie";
import MuiThemeProvider from "material-ui/styles/MuiThemeProvider";
import * as React from "react";
import { Fragment } from "react";
import Reboot from "material-ui/Reboot";
import { ApolloClient } from "apollo-client";
import { ApolloProvider } from "react-apollo";
import { BrowserRouter, Route, Switch } from "react-router-dom";
import { HttpLink } from "apollo-link-http";
import { InMemoryCache } from "apollo-cache-inmemory";
import { Provider } from "react-redux";
import { createStore } from "redux";
import { render } from "react-dom";

import { AppRoot } from "./AppRoot";
import CategorySection from "./category";
import theme from "./theme";

const cookies = new Cookies();

const apolloClient = new ApolloClient({
  link: new HttpLink({
    uri: "/dashboard/graphql/",
    credentials: "same-origin",
    headers: {
      "X-CSRFToken": cookies.get("csrftoken")
    }
  }),
  cache: new InMemoryCache()
});
const routerMapping = [
  {
    component: CategorySection,
    path: "categories"
  }
];
const store = createStore(() => {});

render(
  <Provider store={store}>
    <ApolloProvider client={apolloClient}>
      <BrowserRouter basename="/dashboard/next/">
        <MuiThemeProvider theme={theme}>
          <Reboot />
          <AppRoot>
            <Switch>
              {routerMapping.map(route => (
                <Route
                  key={route.path}
                  path={`/${route.path}/`}
                  component={route.component}
                />
              ))}
            </Switch>
          </AppRoot>
        </MuiThemeProvider>
      </BrowserRouter>
    </ApolloProvider>
  </Provider>,
  document.querySelector("#dashboard-app")
);
