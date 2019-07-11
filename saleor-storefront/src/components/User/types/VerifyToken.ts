/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: VerifyToken
// ====================================================

export interface VerifyToken_tokenVerify_user_defaultShippingAddress_country {
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

export interface VerifyToken_tokenVerify_user_defaultShippingAddress {
  __typename: "Address";
  /**
   * The ID of the object.
   */
  id: string;
  firstName: string;
  lastName: string;
  companyName: string;
  streetAddress1: string;
  streetAddress2: string;
  city: string;
  postalCode: string;
  /**
   * Default shop's country
   */
  country: VerifyToken_tokenVerify_user_defaultShippingAddress_country;
  countryArea: string;
  phone: string | null;
}

export interface VerifyToken_tokenVerify_user_defaultBillingAddress_country {
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

export interface VerifyToken_tokenVerify_user_defaultBillingAddress {
  __typename: "Address";
  /**
   * The ID of the object.
   */
  id: string;
  firstName: string;
  lastName: string;
  companyName: string;
  streetAddress1: string;
  streetAddress2: string;
  city: string;
  postalCode: string;
  /**
   * Default shop's country
   */
  country: VerifyToken_tokenVerify_user_defaultBillingAddress_country;
  countryArea: string;
  phone: string | null;
}

export interface VerifyToken_tokenVerify_user_addresses_country {
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

export interface VerifyToken_tokenVerify_user_addresses {
  __typename: "Address";
  /**
   * The ID of the object.
   */
  id: string;
  firstName: string;
  lastName: string;
  companyName: string;
  streetAddress1: string;
  streetAddress2: string;
  city: string;
  postalCode: string;
  /**
   * Default shop's country
   */
  country: VerifyToken_tokenVerify_user_addresses_country;
  countryArea: string;
  phone: string | null;
}

export interface VerifyToken_tokenVerify_user {
  __typename: "User";
  /**
   * The ID of the object.
   */
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  isStaff: boolean;
  defaultShippingAddress: VerifyToken_tokenVerify_user_defaultShippingAddress | null;
  defaultBillingAddress: VerifyToken_tokenVerify_user_defaultBillingAddress | null;
  /**
   * List of all user's addresses.
   */
  addresses: (VerifyToken_tokenVerify_user_addresses | null)[] | null;
}

export interface VerifyToken_tokenVerify {
  __typename: "VerifyToken";
  payload: any | null;
  user: VerifyToken_tokenVerify_user | null;
}

export interface VerifyToken {
  tokenVerify: VerifyToken_tokenVerify | null;
}

export interface VerifyTokenVariables {
  token: string;
}
