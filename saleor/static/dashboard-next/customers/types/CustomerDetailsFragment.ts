/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: CustomerDetailsFragment
// ====================================================

export interface CustomerDetailsFragment_defaultShippingAddress_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface CustomerDetailsFragment_defaultShippingAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: CustomerDetailsFragment_defaultShippingAddress_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface CustomerDetailsFragment_defaultBillingAddress_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface CustomerDetailsFragment_defaultBillingAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: CustomerDetailsFragment_defaultBillingAddress_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface CustomerDetailsFragment {
  __typename: "User";
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  dateJoined: any;
  lastLogin: any | null;
  defaultShippingAddress: CustomerDetailsFragment_defaultShippingAddress | null;
  defaultBillingAddress: CustomerDetailsFragment_defaultBillingAddress | null;
  note: string | null;
  isActive: boolean;
}
