import { InMemoryCache } from "apollo-cache-inmemory";
import { ApolloClient } from "apollo-client";
import { HttpLink } from "apollo-link-http";
import CssBaseline from "material-ui/CssBaseline";
import MuiThemeProvider from "material-ui/styles/MuiThemeProvider";
import * as React from "react";
import { ApolloProvider } from "react-apollo";
import { render } from "react-dom";
import { Provider } from "react-redux";
import { BrowserRouter, Route, Switch } from "react-router-dom";
import { createStore } from "redux";
import * as Cookies from "universal-cookie";

import AppRoot from "./AppRoot";
import CategorySection from "./category";
import "./i18n";
import PageSection from "./page";
import ProductSection from "./products";
import theme from "./theme";

const cookies = new Cookies();

const apolloClient = new ApolloClient({
  cache: new InMemoryCache(),
  link: new HttpLink({
    credentials: "same-origin",
    headers: {
      "X-CSRFToken": cookies.get("csrftoken")
    },
    uri: "/graphql/"
  })
});
const store = createStore(() => undefined);

render(
  <Provider store={store}>
    <ApolloProvider client={apolloClient}>
      <BrowserRouter basename="/dashboard/next/">
        <MuiThemeProvider theme={theme}>
          <CssBaseline />
          <AppRoot>
            <Switch>
              <Route path="/categories" component={CategorySection} />
              <Route path="/pages" component={PageSection} />
              <Route path="/products" component={ProductSection} />
            </Switch>
          </AppRoot>
        </MuiThemeProvider>
      </BrowserRouter>
    </ApolloProvider>
  </Provider>,
  document.querySelector("#dashboard-app")
);
