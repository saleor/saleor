import CssBaseline from "@material-ui/core/CssBaseline";
import MuiThemeProvider from "@material-ui/core/styles/MuiThemeProvider";
import { InMemoryCache } from "apollo-cache-inmemory";
import { ApolloClient, ApolloError } from "apollo-client";
import { createUploadLink } from "apollo-upload-client";
import * as React from "react";
import { ApolloProvider, MutationFn } from "react-apollo";
import { render } from "react-dom";
import { Provider } from "react-redux";
import { BrowserRouter, Route, Switch } from "react-router-dom";
import { createStore } from "redux";
import * as Cookies from "universal-cookie";

import AppRoot from "./AppRoot";
import CategorySection from "./categories";
import { MessageManager } from "./components/messages";
import "./i18n";
import PageSection from "./pages";
import ProductSection from "./products";
import theme from "./theme";

const cookies = new Cookies();

const apolloClient = new ApolloClient({
  cache: new InMemoryCache(),
  link: createUploadLink({
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
          <MessageManager>
            <CssBaseline />
            <AppRoot>
              <Switch>
                <Route path="/categories" component={CategorySection} />
                <Route path="/pages" component={PageSection} />
                <Route path="/products" component={ProductSection} />
              </Switch>
            </AppRoot>
          </MessageManager>
        </MuiThemeProvider>
      </BrowserRouter>
    </ApolloProvider>
  </Provider>,
  document.querySelector("#dashboard-app")
);

export interface ListProps {
  disabled: boolean;
  pageInfo?: {
    hasNextPage: boolean;
    hasPreviousPage: boolean;
  };
  onNextPage: () => void;
  onPreviousPage: () => void;
  onRowClick: (id: string) => () => void;
}
export interface PageListProps extends ListProps {
  onAdd: () => void;
}

export interface UserError {
  field: string;
  message: string;
}

// These interfaces are used in atomic mutation providers, which then are
// combined into one compound mutation provider
export interface PartialMutationProviderProps<T extends {}> {
  onSuccess?: (data: T) => void;
  onError?: (error: ApolloError) => void;
}
export interface PartialMutationProviderOutput<
  TData extends {} = {},
  TVariables extends {} = {}
> {
  data: TData;
  loading: boolean;
  mutate: (variables: TVariables) => void;
}
export type PartialMutationProviderRenderProps<
  TData extends {} = {},
  TVariables extends {} = {}
> = (
  props: {
    data: TData;
    loading: boolean;
    error?: ApolloError;
    mutate: MutationFn<TData, TVariables>;
  }
) => React.ReactElement<any>;

export interface MutationProviderProps {
  onError?: (error: ApolloError) => void;
}
export type MutationProviderRenderProps<T> = (
  props: T & { errors: UserError[] }
) => React.ReactElement<any>;
