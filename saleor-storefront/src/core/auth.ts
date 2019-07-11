import { ApolloLink } from "apollo-link";
import { setContext } from "apollo-link-context";
import { ErrorResponse, onError } from "apollo-link-error";
import * as React from "react";

export function getAuthToken(): string | null {
  try {
    return localStorage.getItem("token");
  } catch {
    return null;
  }
}

export function setAuthToken(token: string): void {
  localStorage.setItem("token", token);
}

export function removeAuthToken(): void {
  localStorage.removeItem("token");
}

interface ResponseError extends ErrorResponse {
  networkError?: Error & {
    statusCode?: number;
    bodyText?: string;
  };
}

export const invalidTokenLinkWithTokenHandlerComponent = (
  component: React.ComponentClass
): { component: React.FC<any>; link: ApolloLink } => {
  // tslint:disable-next-line:no-empty
  let tokenExpirationCallback = () => {};

  const tokenExpirationHandler = callback => {
    tokenExpirationCallback = callback;
  };
  const extendedComponent = props => {
    return React.createElement(component, {
      ...props,
      tokenExpirationHandler,
    });
  };
  const link = onError((error: ResponseError) => {
    if (error.networkError && error.networkError.statusCode === 401) {
      tokenExpirationCallback();
    }
  });
  return { component: extendedComponent, link };
};

export const authLink = setContext((_, context) => {
  const authToken = getAuthToken();
  if (authToken) {
    return {
      ...context,
      headers: {
        ...context.headers,
        Authorization: authToken ? `JWT ${authToken}` : null,
      },
    };
  } else {
    return context;
  }
});
