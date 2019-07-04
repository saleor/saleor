/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AuthorizationKeyType } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: AuthorizationKeyDelete
// ====================================================

export interface AuthorizationKeyDelete_authorizationKeyDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface AuthorizationKeyDelete_authorizationKeyDelete_shop_authorizationKeys {
  __typename: "AuthorizationKey";
  key: string;
  name: AuthorizationKeyType;
}

export interface AuthorizationKeyDelete_authorizationKeyDelete_shop_domain {
  __typename: "Domain";
  host: string;
}

export interface AuthorizationKeyDelete_authorizationKeyDelete_shop {
  __typename: "Shop";
  authorizationKeys: (AuthorizationKeyDelete_authorizationKeyDelete_shop_authorizationKeys | null)[];
  description: string | null;
  domain: AuthorizationKeyDelete_authorizationKeyDelete_shop_domain;
  name: string;
}

export interface AuthorizationKeyDelete_authorizationKeyDelete {
  __typename: "AuthorizationKeyDelete";
  errors: AuthorizationKeyDelete_authorizationKeyDelete_errors[] | null;
  shop: AuthorizationKeyDelete_authorizationKeyDelete_shop | null;
}

export interface AuthorizationKeyDelete {
  authorizationKeyDelete: AuthorizationKeyDelete_authorizationKeyDelete | null;
}

export interface AuthorizationKeyDeleteVariables {
  keyType: AuthorizationKeyType;
}
