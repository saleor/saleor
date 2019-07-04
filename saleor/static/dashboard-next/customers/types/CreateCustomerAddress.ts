/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AddressInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: CreateCustomerAddress
// ====================================================

export interface CreateCustomerAddress_addressCreate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface CreateCustomerAddress_addressCreate_address_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface CreateCustomerAddress_addressCreate_address {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: CreateCustomerAddress_addressCreate_address_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface CreateCustomerAddress_addressCreate_user_addresses_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface CreateCustomerAddress_addressCreate_user_addresses {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: CreateCustomerAddress_addressCreate_user_addresses_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface CreateCustomerAddress_addressCreate_user_defaultBillingAddress {
  __typename: "Address";
  id: string;
}

export interface CreateCustomerAddress_addressCreate_user_defaultShippingAddress {
  __typename: "Address";
  id: string;
}

export interface CreateCustomerAddress_addressCreate_user {
  __typename: "User";
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  addresses: (CreateCustomerAddress_addressCreate_user_addresses | null)[] | null;
  defaultBillingAddress: CreateCustomerAddress_addressCreate_user_defaultBillingAddress | null;
  defaultShippingAddress: CreateCustomerAddress_addressCreate_user_defaultShippingAddress | null;
}

export interface CreateCustomerAddress_addressCreate {
  __typename: "AddressCreate";
  errors: CreateCustomerAddress_addressCreate_errors[] | null;
  address: CreateCustomerAddress_addressCreate_address | null;
  user: CreateCustomerAddress_addressCreate_user | null;
}

export interface CreateCustomerAddress {
  addressCreate: CreateCustomerAddress_addressCreate | null;
}

export interface CreateCustomerAddressVariables {
  id: string;
  input: AddressInput;
}
