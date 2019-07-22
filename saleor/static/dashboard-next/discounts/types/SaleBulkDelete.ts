/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: SaleBulkDelete
// ====================================================

export interface SaleBulkDelete_saleBulkDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface SaleBulkDelete_saleBulkDelete {
  __typename: "SaleBulkDelete";
  errors: SaleBulkDelete_saleBulkDelete_errors[] | null;
}

export interface SaleBulkDelete {
  saleBulkDelete: SaleBulkDelete_saleBulkDelete | null;
}

export interface SaleBulkDeleteVariables {
  ids: (string | null)[];
}
