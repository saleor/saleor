/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AuthorizationKeyInput, AuthorizationKeyType } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: AuthorizationKeyAdd
// ====================================================

export interface AuthorizationKeyAdd_authorizationKeyAdd_errors {
  __typename: "Error";
  /**
   * Name of a field that caused the error. A value of
   *         `null` indicates that the error isn't associated with a particular
   *         field.
   */
  field: string | null;
  /**
   * The error message.
   */
  message: string | null;
}

export interface AuthorizationKeyAdd_authorizationKeyAdd_shop_authorizationKeys {
  __typename: "AuthorizationKey";
  /**
   * Authorization key (client ID).
   */
  key: string;
  /**
   * Name of the authorization backend.
   */
  name: AuthorizationKeyType;
}

export interface AuthorizationKeyAdd_authorizationKeyAdd_shop_companyAddress_country {
  __typename: "CountryDisplay";
  /**
   * Country code.
   */
  code: string;
  /**
   * Country name.
   */
  country: string;
}

export interface AuthorizationKeyAdd_authorizationKeyAdd_shop_companyAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  /**
   * Default shop's country
   */
  country: AuthorizationKeyAdd_authorizationKeyAdd_shop_companyAddress_country;
  countryArea: string;
  firstName: string;
  /**
   * The ID of the object.
   */
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface AuthorizationKeyAdd_authorizationKeyAdd_shop_countries {
  __typename: "CountryDisplay";
  /**
   * Country code.
   */
  code: string;
  /**
   * Country name.
   */
  country: string;
}

export interface AuthorizationKeyAdd_authorizationKeyAdd_shop_domain {
  __typename: "Domain";
  /**
   * The host name of the domain.
   */
  host: string;
}

export interface AuthorizationKeyAdd_authorizationKeyAdd_shop {
  __typename: "Shop";
  /**
   * List of configured authorization keys. Authorization
   *                keys are used to enable third party OAuth authorization
   *                (currently Facebook or Google).
   */
  authorizationKeys: (AuthorizationKeyAdd_authorizationKeyAdd_shop_authorizationKeys | null)[];
  /**
   * Company address
   */
  companyAddress: AuthorizationKeyAdd_authorizationKeyAdd_shop_companyAddress | null;
  /**
   * List of countries available in the shop.
   */
  countries: (AuthorizationKeyAdd_authorizationKeyAdd_shop_countries | null)[];
  /**
   * Shop's description.
   */
  description: string | null;
  /**
   * Shop's domain data.
   */
  domain: AuthorizationKeyAdd_authorizationKeyAdd_shop_domain;
  /**
   * Shop's name.
   */
  name: string;
}

export interface AuthorizationKeyAdd_authorizationKeyAdd {
  __typename: "AuthorizationKeyAdd";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: AuthorizationKeyAdd_authorizationKeyAdd_errors[] | null;
  /**
   * Updated Shop
   */
  shop: AuthorizationKeyAdd_authorizationKeyAdd_shop | null;
}

export interface AuthorizationKeyAdd {
  /**
   * Adds an authorization key.
   */
  authorizationKeyAdd: AuthorizationKeyAdd_authorizationKeyAdd | null;
}

export interface AuthorizationKeyAddVariables {
  input: AuthorizationKeyInput;
  keyType: AuthorizationKeyType;
}
