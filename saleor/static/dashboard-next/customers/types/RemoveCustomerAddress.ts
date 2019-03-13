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

export interface RemoveCustomerAddress_addressDelete {
  __typename: "AddressDelete";
  errors: RemoveCustomerAddress_addressDelete_errors[] | null;
}

export interface RemoveCustomerAddress {
  addressDelete: RemoveCustomerAddress_addressDelete | null;
}

export interface RemoveCustomerAddressVariables {
  id: string;
}
