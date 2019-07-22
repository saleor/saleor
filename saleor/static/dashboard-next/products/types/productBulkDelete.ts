/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: productBulkDelete
// ====================================================

export interface productBulkDelete_productBulkDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface productBulkDelete_productBulkDelete {
  __typename: "ProductBulkDelete";
  errors: productBulkDelete_productBulkDelete_errors[] | null;
}

export interface productBulkDelete {
  productBulkDelete: productBulkDelete_productBulkDelete | null;
}

export interface productBulkDeleteVariables {
  ids: string[];
}
