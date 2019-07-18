/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: CustomerAddressesFragment
// ====================================================

export interface CustomerAddressesFragment_addresses_country {
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

export interface CustomerAddressesFragment_addresses {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  /**
   * Default shop's country
   */
  country: CustomerAddressesFragment_addresses_country;
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

export interface CustomerAddressesFragment_defaultBillingAddress {
  __typename: "Address";
  /**
   * The ID of the object.
   */
  id: string;
}

export interface CustomerAddressesFragment_defaultShippingAddress {
  __typename: "Address";
  /**
   * The ID of the object.
   */
  id: string;
}

export interface CustomerAddressesFragment {
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
  addresses: (CustomerAddressesFragment_addresses | null)[] | null;
  defaultBillingAddress: CustomerAddressesFragment_defaultBillingAddress | null;
  defaultShippingAddress: CustomerAddressesFragment_defaultShippingAddress | null;
}
