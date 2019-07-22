/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: RemoveCustomer
// ====================================================

export interface RemoveCustomer_customerDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface RemoveCustomer_customerDelete {
  __typename: "CustomerDelete";
  errors: RemoveCustomer_customerDelete_errors[] | null;
}

export interface RemoveCustomer {
  customerDelete: RemoveCustomer_customerDelete | null;
}

export interface RemoveCustomerVariables {
  id: string;
}
