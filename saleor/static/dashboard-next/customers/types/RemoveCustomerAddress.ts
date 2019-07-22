/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: RemoveCustomerAddress
// ====================================================

export interface RemoveCustomerAddress_addressDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface RemoveCustomerAddress_addressDelete_user_addresses_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface RemoveCustomerAddress_addressDelete_user_addresses {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: RemoveCustomerAddress_addressDelete_user_addresses_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface RemoveCustomerAddress_addressDelete_user_defaultBillingAddress {
  __typename: "Address";
  id: string;
}

export interface RemoveCustomerAddress_addressDelete_user_defaultShippingAddress {
  __typename: "Address";
  id: string;
}

export interface RemoveCustomerAddress_addressDelete_user {
  __typename: "User";
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  addresses: (RemoveCustomerAddress_addressDelete_user_addresses | null)[] | null;
  defaultBillingAddress: RemoveCustomerAddress_addressDelete_user_defaultBillingAddress | null;
  defaultShippingAddress: RemoveCustomerAddress_addressDelete_user_defaultShippingAddress | null;
}

export interface RemoveCustomerAddress_addressDelete {
  __typename: "AddressDelete";
  errors: RemoveCustomerAddress_addressDelete_errors[] | null;
  user: RemoveCustomerAddress_addressDelete_user | null;
}

export interface RemoveCustomerAddress {
  addressDelete: RemoveCustomerAddress_addressDelete | null;
}

export interface RemoveCustomerAddressVariables {
  id: string;
}
