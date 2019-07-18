/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: CustomerAddresses
// ====================================================

export interface CustomerAddresses_user_addresses_country {
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

export interface CustomerAddresses_user_addresses {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  /**
   * Default shop's country
   */
  country: CustomerAddresses_user_addresses_country;
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

export interface CustomerAddresses_user_defaultBillingAddress {
  __typename: "Address";
  /**
   * The ID of the object.
   */
  id: string;
}

export interface CustomerAddresses_user_defaultShippingAddress {
  __typename: "Address";
  /**
   * The ID of the object.
   */
  id: string;
}

export interface CustomerAddresses_user {
  __typename: "User";
  /**
   * The ID of the object.
   */
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  /**
   * List of all user's addresses.
   */
  addresses: (CustomerAddresses_user_addresses | null)[] | null;
  defaultBillingAddress: CustomerAddresses_user_defaultBillingAddress | null;
  defaultShippingAddress: CustomerAddresses_user_defaultShippingAddress | null;
}

export interface CustomerAddresses {
  /**
   * Lookup an user by ID.
   */
  user: CustomerAddresses_user | null;
}

export interface CustomerAddressesVariables {
  id: string;
}
