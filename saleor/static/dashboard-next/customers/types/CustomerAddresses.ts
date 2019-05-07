/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: CustomerAddresses
// ====================================================

export interface CustomerAddresses_user_addresses_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface CustomerAddresses_user_addresses {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: CustomerAddresses_user_addresses_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface CustomerAddresses_user_defaultBillingAddress {
  __typename: "Address";
  id: string;
}

export interface CustomerAddresses_user_defaultShippingAddress {
  __typename: "Address";
  id: string;
}

export interface CustomerAddresses_user {
  __typename: "User";
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  addresses: (CustomerAddresses_user_addresses | null)[] | null;
  defaultBillingAddress: CustomerAddresses_user_defaultBillingAddress | null;
  defaultShippingAddress: CustomerAddresses_user_defaultShippingAddress | null;
}

export interface CustomerAddresses {
  user: CustomerAddresses_user | null;
}

export interface CustomerAddressesVariables {
  id: string;
}
