import "jquery.cookie";
import MuiThemeProvider from "material-ui/styles/MuiThemeProvider";
import React, { Fragment } from "react";
import Reboot from "material-ui/Reboot";
import { ApolloClient } from "apollo-client";
import { ApolloProvider } from "react-apollo";
import { BrowserRouter, Route, Switch } from "react-router-dom";
import { HttpLink } from "apollo-link-http";
import { InMemoryCache } from "apollo-cache-inmemory";
import { Provider } from "react-redux";
import { createStore } from "redux";
import { render } from "react-dom";

import CategorySection from "./category";
import theme from "./theme";

const apolloClient = new ApolloClient({
  link: new HttpLink({
    uri: "/dashboard/graphql/",
    credentials: "same-origin",
    headers: {
      "X-CSRFToken": $.cookie("csrftoken")
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
          <Switch>
            {routerMapping.map(route => (
              <Fragment key={route.path}>
                <Route path={`/${route.path}/`} component={route.component} />
              </Fragment>
            ))}
          </Switch>
        </MuiThemeProvider>
      </BrowserRouter>
    </ApolloProvider>
  </Provider>,
  document.querySelector("#dashboard-app")
);
