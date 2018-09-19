/* tslint:disable */
// This file was automatically generated and should not be edited.

import { AddressCountry } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: AddressFragment
// ====================================================

export interface AddressFragment {
  __typename: "Address";
  id: string;
  city: string;
  cityArea: string;
  companyName: string;
  country: AddressCountry;
  countryArea: string;
  firstName: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}
