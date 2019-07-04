/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: AddressFragment
// ====================================================

export interface AddressFragment_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface AddressFragment {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: AddressFragment_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}
