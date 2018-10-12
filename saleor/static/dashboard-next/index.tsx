import CssBaseline from "@material-ui/core/CssBaseline";
import MuiThemeProvider from "@material-ui/core/styles/MuiThemeProvider";
import { InMemoryCache } from "apollo-cache-inmemory";
import { ApolloClient, ApolloError } from "apollo-client";
import { setContext } from "apollo-link-context";
import { ErrorResponse, onError } from "apollo-link-error";
import { createUploadLink } from "apollo-upload-client";
import * as React from "react";
import { ApolloProvider, MutationFn } from "react-apollo";
import { render } from "react-dom";
import { BrowserRouter, Route, Switch } from "react-router-dom";
import * as Cookies from "universal-cookie";

import Auth, { getAuthToken, removeAuthToken } from "./auth";
import AuthProvider from "./auth/AuthProvider";
import LoginLoading from "./auth/components/LoginLoading/LoginLoading";
import SectionRoute from "./auth/components/SectionRoute";
import { hasPermission } from "./auth/misc";
import CategorySection from "./categories";
import { DateProvider } from "./components/DateFormatter";
import { LocaleProvider } from "./components/Locale";
import { MessageManager } from "./components/messages";
import ConfigurationSection, { configurationMenu } from "./configuration";
import HomePage from "./home";
import "./i18n";
import { NotFound } from "./NotFound";
import OrdersSection from "./orders";
import PageSection from "./pages";
import ProductSection from "./products";
import ProductTypesSection from "./productTypes";
import StaffSection from "./staff";
import theme from "./theme";
import { PermissionEnum } from './types/globalTypes';


const cookies = new Cookies();

interface ResponseError extends ErrorResponse {
  networkError?: Error & {
    statusCode?: number;
    bodyText?: string;
  };
}

const invalidTokenLink = onError((error: ResponseError) => {
  if (error.networkError && error.networkError.statusCode === 401) {
    removeAuthToken();
  }
});

const authLink = setContext((_, context) => {
  const authToken = getAuthToken();
  return {
    ...context,
    headers: {
      ...context.headers,
      Authorization: authToken ? `JWT ${authToken}` : null
    }
  };
});

const uploadLink = createUploadLink({
  credentials: "same-origin",
  headers: {
    "X-CSRFToken": cookies.get("csrftoken")
  },
  uri: "/graphql/"
});

const apolloClient = new ApolloClient({
  cache: new InMemoryCache(),
  link: invalidTokenLink.concat(authLink.concat(uploadLink))
});

export const appMountPoint = "/dashboard/next/";

render(
  <ApolloProvider client={apolloClient}>
    <BrowserRouter basename={appMountPoint}>
      <MuiThemeProvider theme={theme}>
        <DateProvider>
          <LocaleProvider>
            <MessageManager>
              <CssBaseline />
              <AuthProvider>
                {({
                  hasToken,
                  isAuthenticated,
                  tokenAuthLoading,
                  tokenVerifyLoading,
                  user
                }) => {
                  return isAuthenticated &&
                    !tokenAuthLoading &&
                    !tokenVerifyLoading ? (
                    <Switch>
                      <SectionRoute exact path="/" component={HomePage} />
                      <SectionRoute
                        permissions={[PermissionEnum.MANAGE_PRODUCTS]}
                        path="/categories"
                        component={CategorySection}
                      />
                      <SectionRoute
                        permissions={[PermissionEnum.MANAGE_PAGES]}
                        path="/pages"
                        component={PageSection}
                      />
                      <SectionRoute
                        permissions={[PermissionEnum.MANAGE_ORDERS]}
                        path="/orders"
                        component={OrdersSection}
                      />
                      <SectionRoute
                        permissions={[PermissionEnum.MANAGE_PRODUCTS]}
                        path="/products"
                        component={ProductSection}
                      />
                      <SectionRoute
                        permissions={[PermissionEnum.MANAGE_PRODUCTS]}
                        path="/productTypes"
                        component={ProductTypesSection}
                      />
                      <SectionRoute
                        permissions={[PermissionEnum.MANAGE_STAFF]}
                        path="/staff"
                        component={StaffSection}
                      />
                      {configurationMenu.filter(menuItem =>
                        hasPermission(menuItem.permission, user)
                      ).length > 0 && (
                        <SectionRoute
                          exact
                          path="/configuration"
                          component={ConfigurationSection}
                        />
                      )}
                      <Route component={NotFound} />
                    </Switch>
                  ) : hasToken && tokenVerifyLoading ? (
                    <LoginLoading />
                  ) : (
                    <Auth loading={tokenAuthLoading} />
                  );
                }}
              </AuthProvider>
            </MessageManager>
          </LocaleProvider>
        </DateProvider>
      </MuiThemeProvider>
    </BrowserRouter>
  </ApolloProvider>,
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
export interface PartialMutationProviderProps<T extends {} = {}> {
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
    called?: boolean;
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
