/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: CustomerAddressesFragment
// ====================================================

export interface CustomerAddressesFragment_addresses_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface CustomerAddressesFragment_addresses {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: CustomerAddressesFragment_addresses_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface CustomerAddressesFragment_defaultBillingAddress {
  __typename: "Address";
  id: string;
}

export interface CustomerAddressesFragment_defaultShippingAddress {
  __typename: "Address";
  id: string;
}

export interface CustomerAddressesFragment {
  __typename: "User";
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  addresses: (CustomerAddressesFragment_addresses | null)[] | null;
  defaultBillingAddress: CustomerAddressesFragment_defaultBillingAddress | null;
  defaultShippingAddress: CustomerAddressesFragment_defaultShippingAddress | null;
}
