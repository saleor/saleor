import { defaultDataIdFromObject, InMemoryCache } from "apollo-cache-inmemory";
import { ApolloClient } from "apollo-client";
import { ApolloLink } from "apollo-link";
import { BatchHttpLink } from "apollo-link-batch-http";
import { setContext } from "apollo-link-context";
import { ErrorResponse, onError } from "apollo-link-error";
import { createUploadLink } from "apollo-upload-client";
import * as React from "react";
import { ApolloProvider } from "react-apollo";
import { render } from "react-dom";
import { BrowserRouter, Route, Switch } from "react-router-dom";
import * as Cookies from "universal-cookie";

import { getAuthToken, removeAuthToken } from "./auth";
import AuthProvider from "./auth/AuthProvider";
import LoginLoading from "./auth/components/LoginLoading/LoginLoading";
import SectionRoute from "./auth/components/SectionRoute";
import { hasPermission } from "./auth/misc";
import Login from "./auth/views/Login";
import CategorySection from "./categories";
import CollectionSection from "./collections";
import { AppProgressProvider } from "./components/AppProgress";
// import { ConfirmFormLeaveDialog } from "./components/ConfirmFormLeaveDialog";
import { DateProvider } from "./components/Date";
import { FormProvider } from "./components/Form";
import { LocaleProvider } from "./components/Locale";
import { MessageManager } from "./components/messages";
import { ShopProvider } from "./components/Shop";
import ThemeProvider from "./components/Theme";
import { WindowTitle } from "./components/WindowTitle";
import ConfigurationSection, { configurationMenu } from "./configuration";
import { CustomerSection } from "./customers";
import DiscountSection from "./discounts";
import HomePage from "./home";
import i18n from "./i18n";
import { NotFound } from "./NotFound";
import OrdersSection from "./orders";
import PageSection from "./pages";
import ProductSection from "./products";
import ProductTypesSection from "./productTypes";
import ShippingSection from "./shipping";
import SiteSettingsSection from "./siteSettings";
import StaffSection from "./staff";
import TaxesSection from "./taxes";
import TranslationsSection from "./translations";
import { PermissionEnum } from "./types/globalTypes";

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

const linkOptions = {
  credentials: "same-origin",
  headers: {
    "X-CSRFToken": cookies.get("csrftoken")
  },
  uri: "/graphql/"
};
const uploadLink = createUploadLink(linkOptions);
const batchLink = new BatchHttpLink(linkOptions);

const link = ApolloLink.split(
  operation => operation.getContext().useBatching,
  batchLink,
  uploadLink
);

const apolloClient = new ApolloClient({
  cache: new InMemoryCache({
    dataIdFromObject: (obj: any) => {
      // We need to set manually shop's ID, since it is singleton and
      // API does not return its ID
      if (obj.__typename === "Shop") {
        return "shop";
      }
      return defaultDataIdFromObject(obj);
    }
  }),
  link: invalidTokenLink.concat(authLink.concat(link))
});

export const appMountPoint = "/dashboard/next/";

const App: React.FC = () => {
  const isDark = localStorage.getItem("theme") === "true";

  return (
    <FormProvider>
      <ApolloProvider client={apolloClient}>
        <BrowserRouter basename={appMountPoint}>
          <ThemeProvider isDefaultDark={isDark}>
            <DateProvider>
              <LocaleProvider>
                <MessageManager>
                  <AppProgressProvider>
                    <ShopProvider>
                      <WindowTitle title={i18n.t("Dashboard")} />
                      {/* FIXME: #3424 */}
                      {/* <ConfirmFormLeaveDialog /> */}
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
                              <SectionRoute
                                exact
                                path="/"
                                component={HomePage}
                              />
                              <SectionRoute
                                permissions={[PermissionEnum.MANAGE_PRODUCTS]}
                                path="/categories"
                                component={CategorySection}
                              />
                              <SectionRoute
                                permissions={[PermissionEnum.MANAGE_PRODUCTS]}
                                path="/collections"
                                component={CollectionSection}
                              />
                              <SectionRoute
                                permissions={[PermissionEnum.MANAGE_USERS]}
                                path="/customers"
                                component={CustomerSection}
                              />
                              <SectionRoute
                                permissions={[PermissionEnum.MANAGE_DISCOUNTS]}
                                path="/discounts"
                                component={DiscountSection}
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
                                path="/product-types"
                                component={ProductTypesSection}
                              />
                              <SectionRoute
                                permissions={[PermissionEnum.MANAGE_STAFF]}
                                path="/staff"
                                component={StaffSection}
                              />
                              <SectionRoute
                                permissions={[PermissionEnum.MANAGE_SETTINGS]}
                                path="/site-settings"
                                component={SiteSettingsSection}
                              />
                              <SectionRoute
                                permissions={[PermissionEnum.MANAGE_SETTINGS]}
                                path="/taxes"
                                component={TaxesSection}
                              />
                              <SectionRoute
                                permissions={[PermissionEnum.MANAGE_SHIPPING]}
                                path="/shipping"
                                component={ShippingSection}
                              />
                              <SectionRoute
                                permissions={[
                                  PermissionEnum.MANAGE_TRANSLATIONS
                                ]}
                                path="/translations"
                                component={TranslationsSection}
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
                            <Login loading={tokenAuthLoading} />
                          );
                        }}
                      </AuthProvider>
                    </ShopProvider>
                  </AppProgressProvider>
                </MessageManager>
              </LocaleProvider>
            </DateProvider>
          </ThemeProvider>
        </BrowserRouter>
      </ApolloProvider>
    </FormProvider>
  );
};

render(<App />, document.querySelector("#dashboard-app"));
