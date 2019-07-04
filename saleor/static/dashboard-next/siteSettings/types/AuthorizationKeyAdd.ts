/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AuthorizationKeyInput, AuthorizationKeyType } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: AuthorizationKeyAdd
// ====================================================

export interface AuthorizationKeyAdd_authorizationKeyAdd_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface AuthorizationKeyAdd_authorizationKeyAdd_shop_authorizationKeys {
  __typename: "AuthorizationKey";
  key: string;
  name: AuthorizationKeyType;
}

export interface AuthorizationKeyAdd_authorizationKeyAdd_shop_domain {
  __typename: "Domain";
  host: string;
}

export interface AuthorizationKeyAdd_authorizationKeyAdd_shop {
  __typename: "Shop";
  authorizationKeys: (AuthorizationKeyAdd_authorizationKeyAdd_shop_authorizationKeys | null)[];
  description: string | null;
  domain: AuthorizationKeyAdd_authorizationKeyAdd_shop_domain;
  name: string;
}

export interface AuthorizationKeyAdd_authorizationKeyAdd {
  __typename: "AuthorizationKeyAdd";
  errors: AuthorizationKeyAdd_authorizationKeyAdd_errors[] | null;
  shop: AuthorizationKeyAdd_authorizationKeyAdd_shop | null;
}

export interface AuthorizationKeyAdd {
  authorizationKeyAdd: AuthorizationKeyAdd_authorizationKeyAdd | null;
}

export interface AuthorizationKeyAddVariables {
  input: AuthorizationKeyInput;
  keyType: AuthorizationKeyType;
}
