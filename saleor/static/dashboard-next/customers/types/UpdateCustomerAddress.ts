/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AddressInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: UpdateCustomerAddress
// ====================================================

export interface UpdateCustomerAddress_addressUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface UpdateCustomerAddress_addressUpdate_address_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface UpdateCustomerAddress_addressUpdate_address {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: UpdateCustomerAddress_addressUpdate_address_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface UpdateCustomerAddress_addressUpdate {
  __typename: "AddressUpdate";
  errors: UpdateCustomerAddress_addressUpdate_errors[] | null;
  address: UpdateCustomerAddress_addressUpdate_address | null;
}

export interface UpdateCustomerAddress {
  addressUpdate: UpdateCustomerAddress_addressUpdate | null;
}

export interface UpdateCustomerAddressVariables {
  id: string;
  input: AddressInput;
}
