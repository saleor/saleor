/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: BulkRemoveCustomers
// ====================================================

export interface BulkRemoveCustomers_customerBulkDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface BulkRemoveCustomers_customerBulkDelete {
  __typename: "CustomerBulkDelete";
  errors: BulkRemoveCustomers_customerBulkDelete_errors[] | null;
}

export interface BulkRemoveCustomers {
  customerBulkDelete: BulkRemoveCustomers_customerBulkDelete | null;
}

export interface BulkRemoveCustomersVariables {
  ids: (string | null)[];
}
