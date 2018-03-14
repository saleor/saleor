import { InMemoryCache } from "apollo-cache-inmemory";
import { ApolloClient } from "apollo-client";
import { HttpLink } from "apollo-link-http";
import MuiThemeProvider from "material-ui/styles/MuiThemeProvider";
import CssBaseline from "material-ui/CssBaseline";
import * as React from "react";
import { Fragment } from "react";
import { ApolloProvider } from "react-apollo";
import { render } from "react-dom";
import { Provider } from "react-redux";
import { BrowserRouter, Route, Switch } from "react-router-dom";
import { createStore } from "redux";
import * as Cookies from "universal-cookie";

import AppRoot from "./AppRoot";
import CategorySection from "./category";
import "./i18n";
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
const store = createStore(() => {});

render(
  <Provider store={store}>
    <ApolloProvider client={apolloClient}>
      <BrowserRouter basename="/dashboard/next/">
        <MuiThemeProvider theme={theme}>
          <CssBaseline />
          <AppRoot>
            <Switch>
              <Route path="/categories" component={CategorySection} />
            </Switch>
          </AppRoot>
        </MuiThemeProvider>
      </BrowserRouter>
    </ApolloProvider>
  </Provider>,
  document.querySelector("#dashboard-app")
);
