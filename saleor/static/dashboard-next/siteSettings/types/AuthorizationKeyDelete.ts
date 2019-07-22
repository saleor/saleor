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

export interface AuthorizationKeyDelete_authorizationKeyDelete_shop_companyAddress_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface AuthorizationKeyDelete_authorizationKeyDelete_shop_companyAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: AuthorizationKeyDelete_authorizationKeyDelete_shop_companyAddress_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface AuthorizationKeyDelete_authorizationKeyDelete_shop_countries {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface AuthorizationKeyDelete_authorizationKeyDelete_shop_domain {
  __typename: "Domain";
  host: string;
}

export interface AuthorizationKeyDelete_authorizationKeyDelete_shop {
  __typename: "Shop";
  authorizationKeys: (AuthorizationKeyDelete_authorizationKeyDelete_shop_authorizationKeys | null)[];
  companyAddress: AuthorizationKeyDelete_authorizationKeyDelete_shop_companyAddress | null;
  countries: (AuthorizationKeyDelete_authorizationKeyDelete_shop_countries | null)[];
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
