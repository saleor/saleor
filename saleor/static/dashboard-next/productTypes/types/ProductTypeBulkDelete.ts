/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: ProductTypeBulkDelete
// ====================================================

export interface ProductTypeBulkDelete_productTypeBulkDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface ProductTypeBulkDelete_productTypeBulkDelete {
  __typename: "ProductTypeBulkDelete";
  errors: ProductTypeBulkDelete_productTypeBulkDelete_errors[] | null;
}

export interface ProductTypeBulkDelete {
  productTypeBulkDelete: ProductTypeBulkDelete_productTypeBulkDelete | null;
}

export interface ProductTypeBulkDeleteVariables {
  ids: (string | null)[];
}
